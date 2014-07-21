__author__ = 'Vincent'
# This class will resample the data depending on different needs
import pandas as pd
import numpy as np


class Resampling:
    """Resampler."""

    def __init__(self):
        """Stuff that must be initialized when this class is created"""

    @staticmethod
    def downsample_data_frame(data_frame, freq="1min", closed_side="left", label="left", data_type="timestamp",
                              method=None):
        """Specify the dateFrame that you want to resample to allow graphs to be not overfilled.
        freq: "1min","1H", "1M", "1S" or any multiples there of
        closed: this shows which side to include in the down sampling. ie, "left", "right"
        label: this is to show how the time stamps will be labelled from. ie, "left", "right"
        kind: Either timestamp or period depending on your need, generally time stamp works better

        Example: downsample(df,freq="5min",closed ="left",label= "left",how ="mean")
        This will then resample the dataframe df into 5 minute intervals and the intervals will be
        recalculated using the mean of the interval. The left value of the interval is excluded
        the timestamp will start on the left side of the interval.

        #df2.resample('1min',how='mean',axis = 0,closed ='right',label = 'left',kind ='timestamp')

        Returns a pandas DataFrame object with name which is the timestamp, it will have
        a reading column, this DataFrame will be resampled the way you need it to be"""

        # this is the resample method
        # Ask kevin about checking type to dataFrame
        # if (type(dateFrameIn) == pd.DateFrame):

        if not data_frame:
            raise ValueError('Invalid DateFrame, Please pass DateFrame with actually data')
        if not (closed_side == "left" and closed_side == "right"):
            raise ValueError("The closed side is incorrect, either it's left or right")
        if not (label == "left" and label == "right"):
            raise ValueError("The label is incorrect, either it's left or right")
        if not (data_type == "timestamp" and data_type == "period"):
            if not data_type:
                raise ValueError("The kind of DateFrame is incorrect, please input the correct type")

        try:
            return_frame = data_frame.resample(freq, how=method, closed=closed_side, label=label, kind=data_type)
        except:
            raise ValueError(
                "The frequency inputted isn't one that Pandas can identify, please input correct frequency")
        return return_frame

        #dateFrameIn.resample('1min',how='mean',axis = 0,closed ='right',label = 'left',kind ='timestamp')

    @staticmethod
    def get_max_value_in_frame(data_frame, column="reading"):
        """
        This will take a Pandas DateFrame
        column: You can choose what column you want to find max and min value
        max, min: just so you can get multiple values from this method back
        :return: no specific return, this will be done via parameters max, min
        """

        if not data_frame:
            raise ValueError('Invalid DateFrame, Please pass DateFrame with actually data')
        try:
            columns = data_frame.ix[:, column]  # check column
            # print(maxCollumn)
            maximum = 0
            if len(columns) == 0:
                raise ValueError("There isn't any data to calculate a min and max")

            for x in range(len(columns)):
                if maximum < columns[x]:
                    maximum = columns[x]

            minimum = maximum
            for x in range(len(columns)):
                if minimum > columns[x]:
                    minimum = columns[x]
            return minimum, maximum  # return the min and max values
            ## return int array
        except:
            raise ValueError("The column %s specified doesn't exist in this Pandas DateFrame", column)

    @staticmethod
    def get_accurate_std_dev(data_frame, column="reading"):
        """
        This will take a Pandas DateFrame
        :return: This will return a Standard Deviation of the Pandas DateFrame with higher accuracy
        """
        if not data_frame:
            raise ValueError('Invalid DateFrame, Please pass DateFrame with actually data')
        try:
            columns = data_frame.ix[:, column]
        except:
            raise ValueError("The column %s doesn't exist in the provided DateFrame", column)

        numpy_columns = np.array(columns)
        std_dev = numpy_columns.std()
        if std_dev == 0:
            raise ValueError("Please input a DateFrame with actual data in")
        return std_dev

    @staticmethod
    def get_frame_std_dev(data_frame, column="reading"):
        """
        This will take a Pandas DateFrame this dataFrame should be resampled
        :return: This will return a Standard Deviation of the Pandas DateFrame
        """
        if not data_frame:
            raise ValueError('Invalid DateFrame, Please pass DateFrame with actually data')
        if len(column) <= 0:
            raise ValueError("Invalid column value to find std on")

        try:
            std_dev = data_frame.std(column)
        except:
            raise ValueError("The column %s doesn't exist in the provided DateFrame", column)

        if std_dev == 0:
            raise ValueError("Please input a DateFrame with actual data in")

        return std_dev

    def get_outliers(self, data_frame, freq="1min", closed_side="left", label="left", data_type="timestamp",
                     column="reading"):
        """
        This will take a Pandas DateFrame this dataFrame should be resampled
        freq,closedVal,LabelVal,kindVal,howVal: are for the resampling and will be handled by the method
        downsampleDateFrame, this will raise a valueError
        column: This is the column you want to see outliers on, generally will be the "reading" column
        Reason for duplicating the default values is for less error checking and can call the downSampleDataFrame method
        without any concern
        :return: This will return list of DateTime that will be all the outliers
        """
        if not data_frame:
            raise ValueError('Invalid DateFrame, Please pass DateFrame with actually data')
        try:
            frame_mean = self.downsample_data_frame(data_frame, freq, closed_side, label, data_type, method="mean")
        except:
            raise ValueError("One of the parameters is incorrect")

        try:
            original_frame = self.downsample_data_frame(data_frame, freq, closed_side, label, data_type)
        except:
            raise ValueError("One of the parameters is incorrect")

        try:
            std_dev = self.get_accurate_std_dev(data_frame, column)
        except:
            raise ValueError("The column doesn't exist")

        outlier = 3 * std_dev

        # Two arrays to get the outliers, the arrays allow us to compare values directly
        # No try is used because if it failed before on column, would fail again

        means = frame_mean.ix[:, column]
        true_values = original_frame.ix[:, column]
        date_time_list = []

        for x in range(len(means)):
            difference = true_values[x] - means[x]
            if difference >= outlier:
                date_time_list.append(str(data_frame.ix[x]))

        return date_time_list

