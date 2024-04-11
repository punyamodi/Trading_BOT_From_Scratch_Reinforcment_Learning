# -*- coding: utf-8 -*-
"""Reinforcement Learning for Stock Market Trading.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/sergejhorvat/Tensorflow2.0_Udemy/blob/master/Reinforcement_Learning_for_Stock_Market_Trading.ipynb

## Stage 1: Installing dependencies and environment setup
"""
import warnings
import tensorflow as tf

# Suppress warnings
tf.get_logger().setLevel('ERROR')
warnings.filterwarnings("ignore")
"""## Stage 2: Importing project dependencies"""

import math
import random
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import pandas_datareader as data_reader

from tqdm import tqdm_notebook, tqdm
from collections import deque

tf.__version__

"""## Stage 3: Building the AI Trader network"""

class AI_Trader():
    def __init__(self, window_size, action_space=3, model_name="AITrader"):  # Stay, Buy, Sell
        self.window_size = window_size
        self.state_size = state_creator(data, 0, window_size + 1).shape[2]
        self.action_space = action_space
        self.memory = deque(maxlen=2000)
        self.inventory = []
        self.model_name = model_name

        # Define hyperparameters
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_final = 0.01
        self.epsilon_decay = 0.995

        # Call a function to build a model through this class constructor
        self.model = self.model_builder()

    def model_builder(self):
        model = tf.keras.models.Sequential()
        model.add(tf.keras.layers.LSTM(units=128, activation='relu', return_sequences=True, input_shape=(self.window_size - 1, self.state_size)))
        model.add(tf.keras.layers.LSTM(units=64, activation='relu'))
        model.add(tf.keras.layers.Dense(units=32, activation='relu'))
        model.add(tf.keras.layers.Dense(units=self.action_space, activation='linear'))
        model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(learning_rate=0.001))
        return model

    # Rest of the code remains the same


  # Trade function that takes state as an input and returns an action
  # to perform in perticular state
    def trade(self, state):
       # Should we perform a renadom generated action or action defined in model?

       # If value from our random generator is smaller or equal to our epsilon
       #     then we will retun a random action from action_space [0-3)
       if random.randint(1, 20) == 5:
         return random.randrange(self.action_space)

       # If our random is greater than epsilon then we will use model to perform action
       actions = self.model.predict(state,verbose=0)
       # return only a one number defining an action (#Stay - 0 , Buy - 1, Sell - 2)
       #    that has maximum probability
       return np.argmax(actions[0])

    def batch_train(self, batch_size):
       batch = []
       for i in range(len(self.memory) - batch_size + 1, len(self.memory)):
          batch.append(self.memory[i])

       for state, action, reward, next_state, done in batch:
          reward = reward
          if not done:
              reward = reward + self.gamma * np.amax(self.model.predict(next_state, verbose=0)[0])
          target = self.model.predict(state, verbose=0)
          target[0][action] = reward
          self.model.fit(state, target, epochs=1, verbose=0)

       if self.epsilon > self.epsilon_final:
          self.epsilon *= self.epsilon_decay

"""## Stage 4: Dataset preprocessing

### Defining helper functions

#### Sigmoid
"""

# Usually used at the end of a network for binary classifictation
# It changes range of input to scale of [0,1]
# So we can normalize input data for comparision day by day if they are on different scale
def sigmoid(x):
  return 1 / (1 + math.exp(-x))

"""#### Price format function"""

def stocks_price_format(n):
  if n < 0:
    return "- $ {0:2f}".format(abs(n))
  else:
    return "$ {0:2f}".format(abs(n))

"""#### Dataset loader"""

# Check the data gathered with pandas data_reader:
dataset = data_reader.DataReader(name="AAPL", data_source="stooq")
print("Data set top rows:", "\n" ,dataset.head())

print("Test some cutting with pandas")
print("Start date: ", str(dataset.index[0]).split()[0])
print("End date: ", str(dataset.index[-1]).split()[0])

def dataset_loader(stock_name, web_data_source="stooq"):

  #Use pandas data reader for reading stock data from warious sources like "yahoo", "google"
  dataset = data_reader.DataReader(name=stock_name, data_source="stooq")

  # Get start and end time to variables from dataset
  start_date = str(dataset.index[0]).split()[0]
  end_date = str(dataset.index[-1]).split()[0]

  # Model will use "Close" column for training
  close = dataset['Close']

  return close

"""### State creator"""

# Data -> dataset to predict from, gathered by data:loader()
# Timestep -> Day in the dataset that we want to predict for [0:datalength]
# window_suze -> how many days in past we want to use to predict current status[1:datalength]
#         Try different setup to see what creates best fit
def state_creator(data, timestep, window_size):
    starting_id = timestep - window_size + 1
    if starting_id >= 0:
        windowed_data = data[starting_id:timestep+1]
    else:
        windowed_data = - starting_id * [data[0]] + list(data[0:timestep+1])

    state = []
    for i in range(window_size - 1):
        state.append([sigmoid(windowed_data[i+1] - windowed_data[i])])

    return np.array([state])

"""### Loading a dataset"""

# Tage data for Apple
stock_name = "AAPL"
data = dataset_loader(stock_name)

"""## Stage 5: Training the AI Trader

### Setting hyper parameters
"""

window_size = 10
episodes = 1 # same as epoch

batch_size = 32
data_samples = len(data) - 1 # discard last value, that we will predict on

"""### Defining the Trader model"""

trader = AI_Trader(window_size)

trader.model.summary()

"""### Training loop"""

for episode in range(1, episodes + 1):

  # To keep track of training process
  # .format populates {} with variables in .format(x,y)
  print("Episode: {}/{}".format(episode, episodes))

  # Create state
  # second parameter is timestep = 0
  state = state_creator(data, 0, window_size + 1)

  total_profit = 0
  # Empty inventory before starting episode
  trader.inventory = []

  # One timestep is one day so number of timesteps we have represent data we have
  # tqdm is used for visualization
  for t in tqdm(range(data_samples)):

    # First we will access action that is going to be taken by model
    action = trader.trade(state)

    # Use action to get to next state(t+)
    next_state = state_creator(data, t+1, window_size + 1)
    # As we did not calculate anything up to this point reward is 0
    reward = 0

    if action == 1 and len(trader.inventory)==0 : #Buying
      # Put buyed stock to inventory to trade with
      trader.inventory.append(data[t])
      print("AI Trader bought: ", stocks_price_format(data[t]))

    # To sell we need to have something in inventory
    elif action == 2 and len(trader.inventory)==1 : #Selling
      # Check buy price, pop removes first value from list
      buy_price = trader.inventory.pop(0)

      # If we gain money (current price - buy price) we have reward
      #    if we lost money then reward is 0
      reward = data[t] - buy_price
      total_profit += data[t] - buy_price
      print("AI Trader sold: ", stocks_price_format(data[t]), " Profit: " + stocks_price_format(data[t] - buy_price) )

    elif action == 0:
      print("Hold")

    # if t is last sample in our dateset we are done
    #     we do not have any steps to perform in current episode
    if t == data_samples - 1:
      done = True
    else:
      done = False

    # Append all data to trader-agent memory, experience buffer
    trader.memory.append((state, action, reward, next_state, done))

    # change state to next state, so we are done with an episode
    state = next_state

    if done:
      print("########################")
      print("TOTAL PROFIT: {}".format(total_profit))
      print("########################")

    # Chekc if we have more information in our memory than batch size
    if len(trader.memory) > batch_size:
      try:
        with tf.device('/device:GPU:0'):  # Use the GPU for training
          trader.batch_train(batch_size)
      except:
        trader.batch_train(batch_size)

  # Save the model every 10 episodes
  if episode % 10 == 0:
    try:
      trader.model.save("ai_trader_{}.h5".format(episode))
    except:
      with tf.device('/device:GPU:0'):  # Use the GPU for saving the model
        trader.model.save("ai_trader_{}.h5".format(episode))