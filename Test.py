import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
import Network
import utils
import os


# from custom_generator import DataGenerator


def _map_fn(image_path):
    image_high_res = tf.io.read_file(image_path)
    image_high_res = tf.image.decode_jpeg(image_high_res, channels=3)
    image_high_res = tf.image.convert_image_dtype(image_high_res, dtype=tf.float32)
    image_high_res = tf.image.random_flip_left_right(image_high_res)
    image_low_res = tf.image.resize(image_high_res, size=[21, 97])
    image_high_res = (image_high_res - 0.5) * 2

    return image_low_res, image_high_res


if __name__ == "__main__":

    # Si no pongo esto casca. Da error de cuDNN
    physical_devices = tf.config.experimental.list_physical_devices('GPU')
    tf.config.experimental.set_memory_growth(physical_devices[0], True)

    allowed_formats = {'png', 'jpg', 'jpeg', 'bmp'}
    data_format = 'channels_last'
    tf.keras.backend.set_image_data_format(data_format)
    print("Keras: ", tf.keras.__version__)
    print("Tensorflow: ", tf.__version__)
    print("Image format: ", tf.keras.backend.image_data_format())
    utils.print_available_devices()

    batch_size = 6
    target_shape = (84, 388)
    downscale_factor = 4

    shared_axis = [1, 2] if data_format == 'channels_last' else [2, 3]
    axis = -1 if data_format == 'channels_last' else 1

    dataset_path = './datasets/Removed/'

    if data_format == 'channels_last':
        target_shape = target_shape + (3,)
        shape = (target_shape[0] // downscale_factor, target_shape[1] // downscale_factor, 3)
    else:
        target_shape = (3,) + target_shape
        shape = (3, target_shape[1] // downscale_factor, target_shape[2] // downscale_factor)

    # list_file_path = 'E:\\TFM\\outputs\\listado_imagenes_test.npy'
    list_file_path = './outputs/listado_imagenes_test.npy'
    if os.path.isfile(list_file_path):
        list_files = np.load(list_file_path)
    else:
        list_files = utils.get_list_of_files(dataset_path)
        np.save(list_file_path, list_files)

    np.random.shuffle(list_files)

    # Dataset creation.
    train_ds = tf.data.Dataset.from_tensor_slices(list_files).map(_map_fn,
                                                                  num_parallel_calls=tf.data.experimental.AUTOTUNE)
    # train_ds = train_ds.shuffle(5000)
    train_ds = train_ds.repeat(count=-1)
    train_ds = train_ds.batch(batch_size)
    train_ds = train_ds.prefetch(tf.data.experimental.AUTOTUNE)

    iterator = train_ds.__iter__()

    model_path = './outputs/checkpoints/SRGAN-VGG54/generator_best.h5'
    model_path2 = './saved_weights/SRGAN-VGG54anterior/generator_best.h5'

    # lr_images, hr_images = batch_gen.next()
    lr_images, hr_images = next(iterator)

    generator = Network.Generator(data_format=data_format, axis=axis, shared_axis=shared_axis).build()
    generator.load_weights(model_path)

    generator2 = Network.Generator(data_format=data_format, axis=axis, shared_axis=shared_axis).build()
    generator2.load_weights(model_path2)

    predicted_images = generator.predict(lr_images)
    predicted_images2 = generator2.predict(lr_images)

    for index in range(batch_size):
        fig = plt.figure()
        ax = fig.add_subplot(3, 1, 1)
        ax.imshow(utils.deprocess_LR(lr_images[index]).astype(np.uint8))
        ax.imshow(utils.deprocess_HR(predicted_images2[index]).astype(np.uint8))
        ax.axis("off")
        ax.set_title("W/o Mask")

        ax = fig.add_subplot(3, 1, 2)
        ax.imshow(utils.deprocess_HR(hr_images[index]).astype(np.uint8))
        ax.axis("off")
        ax.set_title("Original")

        ax = fig.add_subplot(3, 1, 3)
        ax.imshow(utils.deprocess_HR(predicted_images[index]).astype(np.uint8))
        ax.axis("off")
        ax.set_title("10 batch size With_Mask")

        plt.show()
        # fig.savefig('./outputs/salida.png')
