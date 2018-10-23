import os
import boto3
import datetime

ACCESS_KEY = os.environ.get("AWS_ACCESS_ID")
SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
BUCKET_PATH = os.environ.get("BUCKET_PATH")


def clamp(val, minimum=0, maximum=255):
    if val < minimum:
        return minimum
    if val > maximum:
        return maximum
    return int(val)


def colorscale(hexstr, scalefactor):
    """
    Scales a hex string by ``scalefactor``. Returns scaled hex string.

    To darken the color, use a float value between 0 and 1.
    To brighten the color, use a float value greater than 1.

    >>> colorscale("#DF3C3C", .5)
    #6F1E1E
    >>> colorscale("#52D24F", 1.6)
    #83FF7E
    >>> colorscale("#4F75D2", 1)
    #4F75D2
    """

    hexstr = hexstr.strip('#')

    if scalefactor < 0 or len(hexstr) != 6:
        return hexstr

    r, g, b = int(hexstr[:2], 16), int(hexstr[2:4], 16), int(hexstr[4:], 16)

    r = clamp(r * scalefactor)
    g = clamp(g * scalefactor)
    b = clamp(b * scalefactor)

    return "#%02x%02x%02x" % (r, g, b)


def upload_to_aws(charname, imgname):
    s3 = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )

    filename = f'char_data/{charname}.html'
    reportpath = f'reports/{charname}.html'
    imagepath = f'images/{imgname}'
    bucket_name = 'roosterbot'

    s3.upload_file(
        filename,
        bucket_name,
        reportpath,
        ExtraArgs={
            'ContentType': "text/html",
            'ACL': "public-read"
        })

    s3.upload_file(
        imagepath,
        bucket_name,
        imagepath,
        ExtraArgs={
            'ContentType': "image/png",
            'ACL': "public-read"
        })

    html_path = BUCKET_PATH + reportpath
    png_path = BUCKET_PATH + imagepath

    return html_path, png_path


if __name__ == "__main__":
    print(ACCESS_KEY)

    print(upload_to_aws('bustedgun-hyjal'))