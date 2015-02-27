__author__ = 'Martin'

QUAGGANS_LIST_URL = "https://api.guildwars2.com/v2/quaggans"
quaggan_image_urls = []


def get_json(url):
    import urllib.request
    import json
    with urllib.request.urlopen(url) as response:
        str_response = str(response.read().decode("utf-8"))
        return json.loads(str_response)


def get_image(url):
    import urllib.request
    filename, _ = urllib.request.urlretrieve(url)
    from PIL import Image
    return Image.open(filename, "r")


def init_quaggan_image_urls():
    quaggan_ids = get_json(QUAGGANS_LIST_URL)
    for quaggan_id in quaggan_ids:
        quaggan_info_url = QUAGGANS_LIST_URL + "/" + quaggan_id
        quaggan_info = get_json(quaggan_info_url)
        quaggan_image_url = quaggan_info["url"]
        quaggan_image_urls.append(quaggan_image_url)


def get_quaggan_image(width, height):
    from random import choice
    quaggan_image_url = choice(quaggan_image_urls)
    image = get_image(quaggan_image_url)
    original_width, original_height = image.size
    width_scale = float(width) / float(original_width)
    height_scale = float(height) / float(original_height)
    # choose the larger scale so as to fill the whole requested size.
    scale = width_scale if width_scale > height_scale else height_scale
    new_width = int(scale * original_width)
    new_height = int(scale * original_height)
    scaled_image = image.resize((new_width, new_height))
    vertical_crop = (new_height - height) / 2
    horizontal_crop = (new_width - width) / 2
    left_crop = int(horizontal_crop)
    right_crop = int(new_width - horizontal_crop) - 1
    top_crop = int(vertical_crop)
    bottom_crop = int(new_height - vertical_crop) - 1
    return scaled_image.crop((left_crop, top_crop, right_crop, bottom_crop))


done_init = False


def application(environ, start_response):
    global done_init
    log_file = environ["wsgi.errors"]
    try:
        from sys import stderr
        if not done_init:
            print("initting urls now!", file=log_file)
            init_quaggan_image_urls()
            print("got " + str(len(quaggan_image_urls)) + " image URLs", file=log_file)
            done_init = True

        from urllib.parse import parse_qs
        request_params = parse_qs(environ["QUERY_STRING"])
        width = int(request_params["width"][0])
        height = int(request_params["height"][0])
        print("serving request! request_params = " + str(request_params), file=log_file)
        width = int(width)
        height = int(height)

        from io import BytesIO
        output = BytesIO()
        image = get_quaggan_image(width, height)
        image.save(output, format='JPEG')
        start_response('200 OK', [("Content-type", "image/jpeg")])
        return [output.getvalue()]
    except (ValueError, AttributeError, KeyError) as e:
        start_response('404 not found', [("Content-type", "text/plain")])
        return [b"No quaggans to be found :("]


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    srv = make_server('localhost', 8080, application)
    srv.serve_forever()