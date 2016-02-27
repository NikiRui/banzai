import os
from kombu import Connection
from glob import glob
from astropy.io import fits

from pylcogt import dbs
from pylcogt import logs
from pylcogt.images import Image

__author__ = 'cmccully'

logger = logs.get_logger(__name__)


def make_output_directory(pipeline_context, image):
    # Get the telescope from the image
    telescope = dbs.get_telescope(image)
    # Create output directory if necessary
    output_directory = os.path.join(pipeline_context.processed_path, telescope.site,
                                    telescope.instrument, image.dayobs)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    return


def post_to_archive_queue(image_path):
    with Connection('amqp://guest:guest@cerberus.lco.gtn') as conn:
        queue = conn.SimpleQueue('ingest_queue')
        queue.put(image_path)
        queue.close()


def read_images(image_list):
    images = []
    for filename in image_list:
        try:
            image = Image(filename=filename)
            images.append(image)
        except Exception as e:
            logger.error(e)
            continue
    return images


def save_images(pipeline_context, images):
    for image in images:
        image_filename = image.header['ORIGNAME'].replace('00.fits', '90.fits')
        filepath = os.path.join(pipeline_context.processed_path, image_filename)
        image.writeto(filepath)
        if pipeline_context.post_to_archive:
            logger.info('Posting {filename} to the archive'.format(filename=image_filename))
            post_to_archive_queue(filepath)


def make_image_list(pipeline_context):

    search_path = os.path.join(pipeline_context.raw_path)

    # return the list of file and a dummy image configuration
    return glob(search_path + '/*.fits')


def select_images(image_list, image_type):
    images = []
    for filename in image_list:
        try:
            if fits.getval(filename, 'OBSTYPE') == image_type:
                images.append(filename)
        except Exception as e:
            logger.error(e)
            continue

    return images
