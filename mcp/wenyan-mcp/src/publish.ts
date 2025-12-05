/**
 * Custom publish module for WeChat Official Account
 * Uses axios + form-data for reliable multipart/form-data uploads
 * (The original @wenyan-md/core/publish uses formdata-node + fetch which is incompatible with WeChat API)
 */

import axios from "axios";
import FormData from "form-data";
import { createReadStream } from "fs";
import { stat } from "fs/promises";
import * as path from "path";
import { JSDOM } from "jsdom";

const WECHAT_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token";
const WECHAT_DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/add";
const WECHAT_UPLOAD_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material";

const APP_ID = process.env.WECHAT_APP_ID || "";
const APP_SECRET = process.env.WECHAT_APP_SECRET || "";

interface AccessTokenResponse {
    access_token?: string;
    expires_in?: number;
    errcode?: number;
    errmsg?: string;
}

interface UploadResponse {
    media_id?: string;
    url?: string;
    errcode?: number;
    errmsg?: string;
}

interface DraftResponse {
    media_id?: string;
    errcode?: number;
    errmsg?: string;
}

/**
 * Get WeChat access token
 */
async function getAccessToken(appId?: string, appSecret?: string): Promise<string> {
    const id = appId ?? APP_ID;
    const secret = appSecret ?? APP_SECRET;

    const response = await axios.get<AccessTokenResponse>(WECHAT_TOKEN_URL, {
        params: {
            grant_type: "client_credential",
            appid: id,
            secret: secret
        }
    });

    if (response.data.errcode) {
        throw new Error(`获取 Access Token 失败，错误码：${response.data.errcode}，${response.data.errmsg}`);
    }

    if (!response.data.access_token) {
        throw new Error(`获取 Access Token 失败: ${JSON.stringify(response.data)}`);
    }

    return response.data.access_token;
}

/**
 * Upload image to WeChat using axios + form-data
 */
async function uploadImage(imagePath: string, accessToken: string, filename?: string): Promise<UploadResponse> {
    let formData: FormData;
    let finalFilename: string;

    if (imagePath.startsWith("http://") || imagePath.startsWith("https://")) {
        // Download remote image first
        const response = await axios.get(imagePath, { responseType: "arraybuffer" });
        const buffer = Buffer.from(response.data);

        const urlFilename = path.basename(imagePath.split("?")[0]);
        const ext = path.extname(urlFilename);
        finalFilename = filename ?? (ext === "" ? `${urlFilename}.jpg` : urlFilename);

        formData = new FormData();
        formData.append("media", buffer, {
            filename: finalFilename,
            contentType: "image/png"
        });
    } else {
        // Local file
        const stats = await stat(imagePath);
        const baseFilename = path.basename(imagePath);
        const ext = path.extname(baseFilename);
        finalFilename = filename ?? (ext === "" ? `${baseFilename}.jpg` : baseFilename);

        formData = new FormData();
        formData.append("media", createReadStream(imagePath), {
            filename: finalFilename,
            contentType: "image/png",
            knownLength: stats.size
        });
    }

    const response = await axios.post<UploadResponse>(
        `${WECHAT_UPLOAD_URL}?access_token=${accessToken}&type=image`,
        formData,
        {
            headers: {
                ...formData.getHeaders()
            },
            maxContentLength: Infinity,
            maxBodyLength: Infinity
        }
    );

    if (response.data.errcode) {
        throw new Error(`上传失败，错误码：${response.data.errcode}，错误信息：${response.data.errmsg}`);
    }

    // Convert http to https
    if (response.data.url && response.data.url.startsWith("http://")) {
        response.data.url = response.data.url.replace("http://", "https://");
    }

    return response.data;
}

/**
 * Create draft in WeChat Official Account
 */
async function createDraft(
    title: string,
    content: string,
    thumbMediaId: string,
    accessToken: string
): Promise<DraftResponse> {
    const response = await axios.post<DraftResponse>(
        `${WECHAT_DRAFT_URL}?access_token=${accessToken}`,
        {
            articles: [
                {
                    title: title,
                    content: content,
                    thumb_media_id: thumbMediaId
                }
            ]
        }
    );

    if (response.data.errcode) {
        throw new Error(`上传到公众号草稿失败，错误码：${response.data.errcode}，${response.data.errmsg}`);
    }

    return response.data;
}

/**
 * Process HTML content, upload all images and replace src
 */
async function processHtmlImages(
    html: string,
    accessToken: string
): Promise<{ html: string; firstImageId: string }> {
    if (!html.includes("<img")) {
        return { html, firstImageId: "" };
    }

    const dom = new JSDOM(html);
    const document = dom.window.document;
    const images = Array.from(document.querySelectorAll("img")) as HTMLImageElement[];

    let firstImageId = "";

    for (const img of images) {
        const src = img.getAttribute("src");
        if (!src) continue;

        // Skip if already uploaded to WeChat
        if (src.startsWith("https://mmbiz.qpic.cn")) {
            if (!firstImageId) firstImageId = src;
            continue;
        }

        try {
            const uploadResult = await uploadImage(src, accessToken);
            img.setAttribute("src", uploadResult.url!);

            if (!firstImageId && uploadResult.media_id) {
                firstImageId = uploadResult.media_id;
            }
        } catch (e) {
            console.error(`Failed to upload image ${src}:`, e);
            // Keep original src if upload fails
        }
    }

    return { html: dom.serialize(), firstImageId };
}

/**
 * Publish article to WeChat Official Account draft box
 */
export async function publishToDraft(
    title: string,
    content: string,
    cover?: string,
    appId?: string,
    appSecret?: string
): Promise<DraftResponse> {
    // Get access token
    const accessToken = await getAccessToken(appId, appSecret);

    // Clean up content (remove extra newlines around list items)
    const cleanedContent = content
        .replace(/\n<li/g, "<li")
        .replace(/<\/li>\n/g, "</li>");

    // Process images in HTML content
    const { html: processedHtml, firstImageId } = await processHtmlImages(cleanedContent, accessToken);

    // Determine cover image
    let coverMediaId = "";

    if (cover) {
        // Use specified cover
        const coverResult = await uploadImage(cover, accessToken, "cover.jpg");
        coverMediaId = coverResult.media_id!;
    } else if (firstImageId) {
        // Use first image as cover
        if (firstImageId.startsWith("https://mmbiz.qpic.cn")) {
            // Need to re-upload as cover
            const coverResult = await uploadImage(firstImageId, accessToken, "cover.jpg");
            coverMediaId = coverResult.media_id!;
        } else {
            coverMediaId = firstImageId;
        }
    }

    if (!coverMediaId) {
        throw new Error("你必须指定一张封面图或者在正文中至少出现一张图片。");
    }

    // Create draft
    const result = await createDraft(title, processedHtml, coverMediaId, accessToken);

    if (!result.media_id) {
        throw new Error(`上传到公众号草稿失败: ${JSON.stringify(result)}`);
    }

    return result;
}
