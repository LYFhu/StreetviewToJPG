import re
import os
from flask import Flask, render_template, request, send_file
import io
import requests
from PIL import Image
import numpy as np
import py360convert
from concurrent.futures import ThreadPoolExecutor
import math

def parse_streetview_url(url):
    match = re.search(
        r'@([-\d.]+),([-\d.]+),[\d.]+a,([0-9.]+)y,([0-9.]+)h,([0-9.]+)t',
        url
    )
    if not match:
        return None

    pano_match = re.search(r'!1s([^!]+)!', url)
    
    width_match = re.search(r'!7i(\d+)', url)
    height_match = re.search(r'!8i(\d+)', url)
    
    if width_match == 3328: # if gen1
        print("gen1 is not supported")
        return None

    return {
        "lat":     match.group(1),
        "lng":     match.group(2),
        "fov":     match.group(3),
        "heading": match.group(4),
        "pitch":   90 - float(match.group(5)),
        "panoid":  pano_match.group(1) if pano_match else None,
        "pano_width":  int(width_match.group(1)) if width_match else 16384,
        "pano_height": int(height_match.group(1)) if height_match else 8192
    }

def get_grid_size(pano_width, zoom):
    # if gen 2/3/shitcam/shitcam26:
    if pano_width == 13312 and zoom < 5:
        cols = math.ceil((2**zoom)*(3/4))+1
        rows = math.ceil(cols/2)
        print("zoom, cols, rows: ", zoom, cols, rows)
        return cols, rows
    
    # if gen4/smallcam
    if pano_width == 16384:
        cols = 2**zoom
        rows = math.ceil(cols/2)
        return cols, rows
    
    # if gen1:
    if pano_width == 3328:
        return None
    
    print("allah")
    return None

def get_tile(panoid, zoom, x, y):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/maps",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    url = f"https://streetviewpixels-pa.googleapis.com/v1/tile?cb_client=maps_sv.tactile&panoid={panoid}&x={x}&y={y}&zoom={zoom}&nbt=1&fover=2"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("Response error ", response.content[:200])
        return None
    return Image.open(io.BytesIO(response.content))

def stitch_tiles(panoid, zoom, pano_width):
    
    cols, rows = get_grid_size(pano_width, zoom)
    
    canvas = Image.new('RGB', (cols * 512, rows * 512))
    
    def fetch_and_place(args):
        x, y = args
        tile = get_tile(panoid, zoom, x, y)
        if tile is None:
            return None
        return x, y, tile
    
    coords = [(x, y) for y in range(rows) for x in range(cols)]
    
    with ThreadPoolExecutor(max_workers=32) as executor:
        results = executor.map(fetch_and_place, coords)
        if results is None:
            return None
        
    print("results: ", results)
    
    for x, y, tile in results:
        canvas.paste(tile, (x * 512, y * 512))

    # Crop black rows from the bottom
    arr = np.array(canvas)
    non_black_rows = np.any(arr > 0, axis=(1, 2))  # True for rows with any non-black pixel
    last_content_row = np.where(non_black_rows)[0][-1] + 1
    canvas = canvas.crop((0, 0, canvas.width, last_content_row))
    
    canvas = canvas.crop((0, 0, canvas.height*2-1, last_content_row))
    
    return canvas

def crop_panorama(image, heading, fov):
    width, height = image.size
    print(f"size: {image.size}")
    
    heading = int((heading/360)*width)
    
    crop_height = int(height//4)
    crop_width = int(2*crop_height*(1920/1080))
    print("Crop_width: ", crop_width)
    
    
    
    
    
    x1 = (heading - crop_width//2) % width
    x2 = (heading + crop_width//2) % width
    print("x1, x2: ", x1, x2)
    
    if x1 > x2:
        print('1')
        new_image = Image.new('RGB', (crop_width, height-2*crop_height))

        img = image.copy()
        left = img.crop((x1, crop_height, width, 3*crop_height))
        print((x1, crop_height, width, 3*crop_height))
        
        img = image.copy()
        right = img.crop((0, crop_height, x2, 3*crop_height))
        
        # combine left and right
        new_image.paste(left, (0, 0))
        new_image.paste(right, (width-x1, 0))
        print("new size: ", new_image.size)
        return new_image
        
    else: # only one piece
        print('2')
        return image.crop((int((x1/360)*width), crop_height, int(((360-x2)/360)*width), 3*crop_height))
    
def equirect_to_perspective(image, heading, pitch, fov, width=4096, height=2304):
    img_array = np.array(image)
    
    result = py360convert.e2p(
        img_array,
        fov_deg=(fov, fov * height / width),
        u_deg=heading,
        v_deg=-pitch,
        out_hw=(height, width)
    )
    return Image.fromarray(result)

def get_pano_heading(panoid, API_KEY):
    res = requests.get(
        "https://cbks0.google.com/cbk",
        params={"output": "json", "panoid": panoid}
    )
    print('res: ',)
    data = res.json()
    return data["Location"]["originalHeading"]














