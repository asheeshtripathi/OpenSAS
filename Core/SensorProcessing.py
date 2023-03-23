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
import matplotlib.pyplot as plt

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
        self.labels_processed = np.zeros([1000], dtype=int)
        self.iq_raw = np.empty([1000, 102400], dtype=np.complex128)
        self.iq_data = np.empty([1000, 102400], dtype=np.float64)
        self.create_dataset = False
        self.num_samples = 0
        self.model = tf.keras.models.load_model('../../my_model_20230317-140708.h5')
        self.max_size = 1000

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
        # print first 2 samples
        print(data[:2])
        complex_samples = np.array([s[0] + 1j * s[1] for s in data])
        complex_np_samples = np.array(complex_samples, dtype=np.complex64)
        print(complex_np_samples.shape)
        iq_averaged = self.rolling_average_complex(complex_np_samples, 1)

        # Calculate the time axis based on the capture rate and number of samples
        capture_rate = 10.24e6
        capture_time = len(iq_averaged) / capture_rate
        time = np.linspace(0, capture_time, len(iq_averaged))

        # Plot the IQ samples over time
        plt.plot(time, np.real(iq_averaged), label='Real')
        plt.plot(time, np.imag(iq_averaged), label='Imaginary')

        # Set the plot title and axis labels
        plt.title("IQ Samples over Time")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")

        # Add a legend
        plt.legend()

        # Display the plot
        plt.show()
        plt.savefig("iq-time.png")
        plt.clf()

        # iq_data[i] = rolling_average_complex(np.fft.fft(np.array(complex_samples, dtype=np.complex64)), 4)
        #Set FFT size
        fft_size = 128

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
        #self.data = final_data
        # Put the real samples into self.data
        self.data = np.real(iq_averaged)
        new_data = True
        if(self.create_dataset):
            self.append(iq_averaged, final_data, 0)
            # Display the image
            mag_array_norm = spectra / np.max(spectra)
            plt.imshow(mag_array_norm.T, cmap='gray')
            plt.axis('off')
            plt.show()
            plt.savefig("fft-time.png")
            plt.clf()
            return None
        else:
            prediction = self.classifySensorData()
            self.update_csv(prediction, sensor_info, channel_info, 'predictions.csv')
            return prediction.tolist()
    
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
        return predictions[0]

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
            writer.writerow([datetime.datetime.now(), prediction, sensor_id, lat, lon, channel])

    def append(self, raw_data, data, label):
        '''
        Appends data to the dataset.

        Args:
            data (ndarray): The data to append to the dataset.
            labels (ndarray): The binary classification labels for the data.
        '''
        self.iq_raw[self.num_samples] = raw_data
        self.iq_data[self.num_samples] =  data
        self.labels_processed[self.num_samples] = label
        self.num_samples += 1
        print(f"Collected {self.num_samples} samples so far. (Max: {self.max_size})")
        if self.num_samples >= self.max_size:
            self.save()
            self.clear()

    def save(self):
        '''
        Saves the dataset to a local npz file with a timestamped filename.
        '''
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"dataset_fft_{timestamp}.npz"
        np.savez(file_name, X=self.iq_data, y=self.labels_processed)
        np.savez(f"dataset_raw_{timestamp}.npz", X=self.iq_raw, y=self.labels_processed)
        print(f"Saved data to {file_name} successfully.")

    def clear(self):
        '''
        Clears the dataset.
        '''
        self.iq_raw = np.empty([1000, 102400], dtype=np.complex64)
        self.labels_processed = np.zeros([1000], dtype=int)
        self.iq_data = np.empty([1000, 102400], dtype=np.float64)
        self.num_samples = 0