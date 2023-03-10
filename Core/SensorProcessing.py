import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import TensorBoard
import tensorflow as tf
from threading import Thread
import json
import datetime
import csv
import os

class PredictionLogger:
    def __init__(self, filename):
        self.filename = filename
        self.file = open(self.filename, 'a')
        self.predictions = []

    def add_prediction(self, prediction):
        self.predictions.append({'prediction': prediction, 'time': str(datetime.datetime.now())})
        self.save_to_json()

    def save_to_json(self):
        if self.predictions:
            self.file.write(json.dumps(self.predictions[-1]) + '\n')
            self.file.flush()

    def close(self):
        self.file.close()


class SensorProcessor(Thread):
    # Class to store and process sensor data when power level is beyond the threshold
    def __init__(self):
        super(SensorProcessor, self).__init__()
        self.daemon = True
        self.cancelled = False
        # do other initialization here
        self.new_data = False
        self.data = None
        self.model = tf.keras.models.load_model('../../my_model_20230307-213547_acc1.h5')

    def rolling_average_complex(self, arr, window_size):
        """
        Computes the rolling average on a np.complex64 array.

        Parameters:
        -----------
        arr : np.complex64 array
            Input array.
        window_size : int
            Size of the rolling window.

        Returns:
        --------
        out : np.complex64 array
            Output array with the same shape as input array.
        """
        # Split real and imaginary parts
        arr_real = np.real(arr)
        arr_imag = np.imag(arr)

        # Compute rolling average of real and imaginary parts separately
        arr_real_avg = np.convolve(arr_real, np.ones(window_size)/window_size, mode='same')
        arr_imag_avg = np.convolve(arr_imag, np.ones(window_size)/window_size, mode='same')

        # Combine the real and imaginary parts into a complex array
        out = arr_real_avg + 1j*arr_imag_avg

        return out


    def processSensorData(self, data, sensor_info, channel_info):
        # Process the sensor data for classification using the trained model
        # return the processed data
        complex_samples = np.array([s[0] + 1j * s[1] for s in data])
        complex_np_samples = np.array(complex_samples, dtype=np.complex64)
        print(complex_np_samples.shape)
        iq_averaged = self.rolling_average_complex(complex_np_samples, 1)
        # iq_data[i] = rolling_average_complex(np.fft.fft(np.array(complex_samples, dtype=np.complex64)), 4)
        #Set FFT size
        fft_size = 512

        # Compute the number of time slices and FFT size
        num_slices = int(len(iq_averaged) / fft_size)
        
        # Compute the FFT of each time slice
        spectra = np.zeros((num_slices, fft_size))
        for j in range(num_slices):
            start_idx = j * fft_size
            end_idx = start_idx + fft_size
            spectrum = np.abs(np.fft.fft(iq_averaged[start_idx:end_idx]))
            spectra[j] = spectrum
        final_data = spectra.flatten()
        
        print(spectra.shape)
        self.data = final_data
        new_data = True
        predictions = self.classifySensorData()
        self.update_csv(predictions, sensor_info, channel_info, 'predictions.csv')
        return
    
    def run(self):
        """Overloaded Thread.run, runs the update 
        method once per every 10 milliseconds."""

        while not self.cancelled:
            if self.new_data:
                self.classifySensorData()
                sleep(0.01)
        

    def classifySensorData(self):
        # Classify the sensor data using the trained model
        # return the classification result

        # Define the input data
        input_data = [self.data]

        # Convert the input data into a numpy array
        input_data = tf.convert_to_tensor(input_data, dtype=tf.float32)

        # Reshape the input data to match the expected shape of the model
        input_data = tf.reshape(input_data, shape=(-1, 102400))

        # Turn off tracing for the predict function
        tf.config.run_functions_eagerly(True)       

        # Perform the classification
        print("data shape")
        print(self.data.shape)
        predictions = self.model.predict(input_data)

        # Print the predictions
        for i, prediction in enumerate(predictions):
            print('Prediction for sample {}: {}'.format(i+1, prediction[0]))
        self.prediction = predictions

        self.new_data = False
        return predictions

    def update_csv(self, prediction, sensor_info, channel, file_path):
        # Create the CSV file if it doesn't exist
        if not os.path.isfile(file_path):
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['prediction', 'sensor_id', 'lat', 'lon', 'channel'])
        # Convert sensor_info JSON string to a dictionary and extract fields
        sensor_info_dict = sensor_info
        sensor_id = sensor_info_dict['sensor_id']
        lat = sensor_info_dict['lat']
        lon = sensor_info_dict['lon']
        # Append data to the CSV file
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([datetime.now(), prediction[0], sensor_id, lat, lon, channel])

