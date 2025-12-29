#!/usr/bin/env python3
"""
Download images from Notion page.
"""
import os
import json
import re
import requests
from pathlib import Path
from urllib.parse import urlparse, unquote
import time

def sanitize_filename(filename):
    """Remove special characters and spaces from filename."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace all types of spaces (including special unicode spaces) with underscores
    filename = re.sub(r'[\s\u00a0\u202f\u2000-\u200f\u2028-\u202f\u3000]+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    return filename

def extract_meaningful_name(url):
    """Extract meaningful name from Notion URL."""
    # Notion URLs have pattern: attachment%3A<uuid>%3A<filename>.png
    match = re.search(r'%3A([^%?]+?)(?:\?|$)', url)
    if match:
        name = match.group(1)
        # Decode URL encoding
        name = unquote(name)
        # Remove .png extension if it exists, we'll add it back
        name = re.sub(r'\.(png|jpg|jpeg|gif|webp|svg)$', '', name, flags=re.IGNORECASE)
        return name
    return None

def download_image(url, output_path, retries=3):
    """Download an image with retry logic."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://notion.site/',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    }

    for attempt in range(retries):
        try:
            print(f"  Downloading (attempt {attempt + 1}/{retries})...")
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            # Write to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify file size
            file_size = os.path.getsize(output_path)
            if file_size < 100:  # Suspiciously small
                print(f"  Warning: File size is only {file_size} bytes")
                return False

            print(f"  Success! Downloaded {file_size} bytes")
            return True

        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)  # Wait before retry
            else:
                print(f"  Failed after {retries} attempts")
                return False

    return False

def main():
    # Image data from Playwright extraction
    images_json = '''[
  {
    "url": "https://yingru.notion.site/image/attachment%3A79a37751-bb41-4083-b3c9-ed834f6d76ec%3Amulti_turn_baseline_actor_grad_norm_val_test_score_extra_score_deepscaler_aime25.png?table=block&id=256211a5-58b7-8385-8854-81e97167633e&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=1420&userId=&cache=v2",
    "alt": "Figure 1",
    "desc": "Gradient Norm and AIME25 Score under multi-turn TIR training"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3Ab2a7bf07-d6ef-43cb-9a98-59be277cdf8e%3Amulti_turn_failed_base_variance_proxy_proxy3_pure_noise_actor_grad_norm_val_test_score_extra_score_deepscaler_aime25.png?table=block&id=2cd211a5-58b7-8017-8c4d-ff09e54c39cc&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=1420&userId=&cache=v2",
    "alt": "Figure 2",
    "desc": "High gradient variance triggers training collapse"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A5629cec9-7f36-44f7-ae6e-34b255258f36%3Alogprob_ratio_hist_200_Total_Energy_1.png?table=block&id=2cd211a5-58b7-8057-822a-f5e21d0e25d9&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=960&userId=&cache=v2",
    "alt": "Figure 3",
    "desc": "Different sequences exhibit distinct energy"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A77b0cf16-5ab9-412e-abcf-a99f731c107a%3Atob_200_token_position_vs_cum_score_norm_seq4101314.png?table=block&id=2ce211a5-58b7-802e-be2c-d2b7124a4734&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=1060&userId=&cache=v2",
    "alt": "Figure 4",
    "desc": "Realized energy across sequences"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A9bf15825-8148-419d-85e3-ecba0ad2a880%3Atob_200_old_prob_vs_score_norm.png?table=block&id=2ce211a5-58b7-8055-97fb-f925b690754f&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=860&userId=&cache=v2",
    "alt": "Figure 5",
    "desc": "Token Probability vs Logit Gradient Norm"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3Adebb8f6b-1696-4359-8842-14bd6dda7dda%3Aimage.png?table=block&id=2d2211a5-58b7-8009-8a74-d720f9d753f5&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=860&userId=&cache=v2",
    "alt": "Figure 6",
    "desc": "Overview of the Optimal Token Baseline"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3Ad470b129-b4e1-485e-a514-6d0a2b20addf%3Atob_200_token_index_vs_ogb_advantages_advantages_pos_seq211.png?table=block&id=2d1211a5-58b7-8074-8d0a-ec075125cc08&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=660&userId=&cache=v2",
    "alt": "Figure 7a",
    "desc": "Advantage distribution on positive sequences"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3Af6f5462b-9d92-4ea0-8cf1-d007944fe15f%3Atob_200_token_index_vs_ogb_advantages_advantages_neg_seq213.png?table=block&id=2ce211a5-58b7-8093-9d9b-e431bb676bc1&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=660&userId=&cache=v2",
    "alt": "Figure 7b",
    "desc": "Advantage distribution on negative sequences"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A60213ccb-8b4b-42d5-8ded-5bc90b07bef5%3Aimage.png?table=block&id=0ab211a5-58b7-834c-b5a0-81658b6c2f14&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=1060&userId=&cache=v2",
    "alt": "Figure 8",
    "desc": "Overview of single-turn and multi-turn training"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3Aa92750c4-8afa-4002-918f-7be14544dd4a%3Asingle_turn_8B_collapse_base_variance_proxy_proxy3_pure_noise_actor_grad_norm.png?table=block&id=2c5211a5-58b7-80a9-ad3c-f48218e73a55&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=1420&userId=&cache=v2",
    "alt": "Figure 9a",
    "desc": "Gradient Variance and Gradient Norm - single-turn zero-reasoning"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A2e1bb578-e57f-47bf-a05c-825e6e02acd4%3Amulti_turn_collapse_base_variance_proxy_proxy3_pure_noise_actor_grad_norm.png?table=block&id=2c5211a5-58b7-8082-95b6-cd29b4b0de4c&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=1420&userId=&cache=v2",
    "alt": "Figure 9b",
    "desc": "Gradient Variance and Gradient Norm - multi-turn TIR"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A407a66be-5c51-45bd-91d5-9c4eb90d121a%3Asingle_turn_8B_mismatch_base_rollout_correction_log_ppl_abs_diff_rollout_correction_kl.png?table=block&id=2c5211a5-58b7-80d0-8d61-d8baac244874&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=1420&userId=&cache=v2",
    "alt": "Figure 10a",
    "desc": "Training-Rollout PPL Gap and KL Divergence - single-turn"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A3b151d7e-740e-4e85-b4ca-e9c5fd70a7fd%3Amulti_turn_mismatch_base_rollout_correction_log_ppl_abs_diff_rollout_correction_kl.png?table=block&id=2c5211a5-58b7-80a4-8adc-d5fda11edf38&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=1420&userId=&cache=v2",
    "alt": "Figure 10b",
    "desc": "Training-Rollout PPL Gap and KL Divergence - multi-turn"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A1ee5cc47-4ed6-42ed-9fb5-258f0dd1f80b%3Asingle_turn_N_step_val_test_score_extra_score_deepscaler_aime25.png?table=block&id=2d3211a5-58b7-8041-bd63-e25f696b5dd6&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=660&userId=&cache=v2",
    "alt": "Figure 11a-1",
    "desc": "Ablation study of group size - single-turn by step"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A02f6fdd9-cc7e-485f-88a6-5f2b89076c3a%3Asingle_token_N_2.png?table=block&id=2d3211a5-58b7-807a-845b-d679e35e101d&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=660&userId=&cache=v2",
    "alt": "Figure 11a-2",
    "desc": "Ablation study of group size - single-turn by token budget"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A1e18a28f-2f27-4623-a6bb-3fc7071900d6%3Amulti_turn_N_step_val_test_score_extra_score_deepscaler_aime25.png?table=block&id=2d3211a5-58b7-8020-ae66-d6a010ebd640&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=660&userId=&cache=v2",
    "alt": "Figure 11b-1",
    "desc": "Ablation study of group size - multi-turn by step"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A7013bf5e-8dbb-4b71-beae-f721db2af532%3Amulti_token_N_2.png?table=block&id=2d3211a5-58b7-80b9-a798-ffc66a5a4fe6&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=660&userId=&cache=v2",
    "alt": "Figure 11b-2",
    "desc": "Ablation study of group size - multi-turn by token budget"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3Aeae0a243-8e58-4619-beff-9742cf1b5d0b%3Atob_200_total_lengths_vs_total_score_norm.png?table=block&id=2cc211a5-58b7-8003-902f-d351708c6166&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=660&userId=&cache=v2",
    "alt": "Figure 12a",
    "desc": "Total energy and response length - global batch"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3Ae76698db-3a82-428e-81c6-f6b203922727%3Alogprob_ratio_hist_200_1_re_rank.png?table=block&id=2d2211a5-58b7-80eb-97bc-f1f13e3ae773&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=660&userId=&cache=v2",
    "alt": "Figure 12b",
    "desc": "Total energy and response length - local intra-group"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A5a7947ed-1c2c-4279-9641-388c91df5597%3Asingle_turn_8B_OB_score_variance_proxy_proxy3_pure_noise_val_test_score_extra_score_deepscaler_aime25.png?table=block&id=2c5211a5-58b7-80b2-995a-e0c7d8560378&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=1420&userId=&cache=v2",
    "alt": "Figure 13a",
    "desc": "Gradient Variance with Logit-Gradient Proxy vs Length"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A9bb2c688-667e-4bba-a010-799fcaf7051c%3Asingle_turn_8B_score_variance_proxy_proxy3_pure_noise_val_test_score_extra_score_deepscaler_aime25.png?table=block&id=2c5211a5-58b7-80e5-aa09-ec06e750e5b0&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=1420&userId=&cache=v2",
    "alt": "Figure 13b",
    "desc": "OTB with Logit-Gradient Proxy vs Length Approximation"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A3d40336b-4b4e-4ab4-b9de-4efb0e88bc25%3Amulti_turn_groups_combined.png?table=block&id=2d2211a5-58b7-80af-95dd-d289b25d5a2a&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=1420&userId=&cache=v2",
    "alt": "Figure 14",
    "desc": "Ablation studies under longer context and larger models"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3Ab444d3df-af30-4bea-9224-2b7a8ee20294%3Amulti_turn_vs_rollout_corr_actor_grad_norm_val_test_score_extra_score_deepscaler_aime25.png?table=block&id=2d1211a5-58b7-8057-97b0-e18e89f14f1a&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=1420&userId=&cache=v2",
    "alt": "Figure 15",
    "desc": "Comparison with MIS - Gradient Norm and AIME25 Score"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3Acbb29003-717f-49a7-af5d-f3f5090cb438%3Asingle_turn_14B_val_test_score_extra_score_deepscaler_aime25.png?table=block&id=2c5211a5-58b7-8014-9b46-c88beec17d86&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=660&userId=&cache=v2",
    "alt": "Figure 16a",
    "desc": "AIME25 Scores - Naive Implementation"
  },
  {
    "url": "https://yingru.notion.site/image/attachment%3A07b773fb-5e1e-4327-aa28-3326b21dcc9a%3Asingle_turn_14B_geo_val_test_score_extra_score_deepscaler_aime25.png?table=block&id=2c5211a5-58b7-80e8-8268-f7fde2ba459f&spaceId=effaf72e-4449-4e46-8824-1cc2f447196b&width=660&userId=&cache=v2",
    "alt": "Figure 16b",
    "desc": "AIME25 Scores - With Geometric-Level Rejection Mask"
  }
]'''

    images = json.loads(images_json)
    output_dir = Path('/home/limo/ccblog/blog/optimal-token-baseline')
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Download images
    manifest = []
    successful = 0
    failed = []

    for idx, img_info in enumerate(images, 1):
        url = img_info['url']
        alt = img_info.get('alt', '')
        desc = img_info.get('desc', '')

        print(f"\n[{idx}/{len(images)}] Processing image:")
        print(f"  URL: {url[:80]}...")
        print(f"  Alt: {alt}")
        print(f"  Description: {desc}")

        # Generate filename from the meaningful part of the URL
        meaningful_name = extract_meaningful_name(url)
        
        if meaningful_name:
            filename = sanitize_filename(meaningful_name) + '.png'
        elif alt:
            filename = sanitize_filename(alt) + '.png'
        else:
            filename = f"figure_{idx:03d}.png"

        # Handle duplicates
        output_path = output_dir / filename
        counter = 1
        while output_path.exists():
            name, ext = os.path.splitext(filename)
            output_path = output_dir / f"{name}_{counter}{ext}"
            counter += 1

        print(f"  Saving to: {output_path}")

        # Download
        if download_image(url, output_path):
            successful += 1
            manifest.append({
                'filename': output_path.name,
                'original_url': url,
                'alt_text': alt,
                'description': desc
            })
        else:
            failed.append({'url': url, 'alt': alt, 'desc': desc})
            # Remove failed download file if it exists
            if output_path.exists():
                output_path.unlink()

    # Save manifest
    manifest_path = output_dir / 'images.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total images found: {len(images)}")
    print(f"Successfully downloaded: {successful}")
    print(f"Failed: {len(failed)}")
    print(f"Output directory: {output_dir}")
    print(f"Manifest file: {manifest_path}")

    if failed:
        print("\nFailed downloads:")
        for f in failed:
            print(f"  - {f['url'][:80]}...")
            print(f"    Alt: {f['alt']}, Desc: {f['desc']}")

    # Verify no spaces in filenames
    print("\nVerifying filenames...")
    files_with_spaces = []
    for file in output_dir.glob('*'):
        if file.is_file() and ' ' in file.name:
            files_with_spaces.append(file.name)

    if files_with_spaces:
        print("WARNING: Found files with spaces in names:")
        for fname in files_with_spaces:
            print(f"  - {fname}")
    else:
        print("All filenames are space-free!")

    print("\nDownloaded images:")
    for item in manifest:
        print(f"  - {item['filename']}")
        if item['description']:
            print(f"    {item['description']}")

if __name__ == '__main__':
    main()
