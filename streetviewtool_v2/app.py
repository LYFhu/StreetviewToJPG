"""Requirements"""
import os
from flask import Flask, render_template, request, send_file
import io
import functions as f
import requests
import base64
from PIL import Image
import py360convert

'''APP'''
app = Flask(__name__)
app.static_folder = os.path.join(os.path.dirname(__file__), 'static')
app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')

'''Handle requests'''
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    '''Process the url'''
    params = f.parse_streetview_url(request.form.get('url'))
    print(params)
    resolution = request.form.get('resolution', '4')
    zoom = int(resolution)
    print("zoom: ", zoom)
    fov = 100
    
    if params is None:
        print('URL not recognized')
        return render_template('index.html', error='Invalid Street View URL')
    else:
        '''Make the request
        api_url = "https://maps.googleapis.com/maps/api/streetview"
        query = {
            "location": f"{params['lat']},{params['lng']}",
            "size":     "640x360",
            "fov":      params['fov'],
            "heading":  params['heading'],
            "pitch":    params['pitch'],
            "key":      "AIzaSyChfEMwZnyIIDowgSpn4efVIT8a_OPuKic"
        }
        response = requests.get(api_url, params=query)
        print("status_code: ", response.status_code)
        '''

        '''Get the images'''
        pano = f.stitch_tiles(params['panoid'], zoom, params['pano_width'])
        #pano = f.get_tile(params['panoid'], 5, 31, 0)
        print("size: ", pano.size)
        #pano.save('test9.jpg')
        
        max_width = int((params['pano_width']/2**(5-zoom)) * (fov/360))
        max_height = int(max_width * 9 / 16)
        
        images = [f.equirect_to_perspective(pano,
                                        float(i*90),
                                        0,
                                        100.0,
                                        width=max_width,
                                        height=max_height) for i in range(4)            
                ]
        images.append(pano)

        images_data = []
        for image in images:
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            buffer.seek(0)
            images_data.append(
                'data:image/jpeg;base64,' + base64.b64encode(buffer.read()).decode('ascii')
            )
            
        print(f"panoid: {params['panoid']}")

        return render_template('index.html', images=images_data)

'''Run the app'''
if __name__ == '__main__':
    app.run(debug=True)

























