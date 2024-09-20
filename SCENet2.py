import numpy as np
import pandas as pd
from tqdm import trange
from time import time

class NeuralNetwork:
    def __init__(self):
        self.status = False
        self.hiddenNeurons = []
        self.dZ = []
        self.Z = []
        self.A = [] 
        self.activation_functions = []
        self.batch_size = 32
        self.alpha = 0.005

    def set(self, alpha=0.005, batch_size=32):
        self.alpha = alpha
        self.batch_size = batch_size

    def digitize(self):
        self.labels = {}
        uniques = sorted(pd.unique(self.y_train))
        for i in range(len(uniques)):
            self.labels[i] = uniques[i]
            self.y_train[self.y_train == uniques[i]] = i
        self.y_train = self.y_train.astype(int)

    def labelize(self, predictions):
        for i in range(len(self.labels)):
            predictions[predictions == i] = self.labels[i]
        return predictions

    def SoftMax(self, Z):
        A = np.exp(Z) / sum(np.exp(Z))
        return A
    
    def activate(self, activation_function:str, Z):
        if activation_function == 'relu':
            return np.maximum(0, Z)
        elif activation_function == 'sigmoid':
            return 1 / (1 + np.exp(-Z)) 
        elif activation_function == 'tanh':
            return 2 / (1+np.exp(-2 * Z)) - 1
        elif activation_function == 'identity':
            return Z
    
    def activate_deriv(self, activation_function:str, Z):
        if activation_function == 'relu':
            return Z > 0
        elif activation_function == 'sigmoid':
            A = 1 / (1 + np.exp(-Z)) 
            return A * (1-A)
        elif activation_function == 'tanh':
            A = 2 / (1+np.exp(-2 * Z)) - 1
            return 1 - A ** 2
        elif activation_function == 'identity':
            return 1

    def one_hot(self, Y):
        one_hot_Y = np.zeros((Y.size, Y.max() + 1))
        one_hot_Y[np.arange(Y.size), Y] = 1
        return one_hot_Y.T
    
    def get_predictions(self, A):
        return np.argmax(A, 0)
    
    def get_accuracy(self, predictions, actual):
        passed = np.sum(predictions == actual)
        accuracy = passed / actual.size
        return accuracy
    
    def prepare_batch(self):
        self.batches = []
        self.batch_labels = []
        self.n_batch = int(self.samples / self.batch_size)
        left_samples = int(self.samples - self.n_batch * self.batch_size)
        start = 0
        self.one_hot_Y = self.one_hot(self.y_train)

        for _ in range(self.n_batch):
            self.batches.append(self.A[0][:,start:start + self.batch_size])
            self.batch_labels.append(self.one_hot_Y[:, start:start + self.batch_size])
            start += self.batch_size

        if left_samples > 0:
            self.batches.append(self.A[0][:,start:])
            self.batch_labels.append(self.one_hot_Y[:,start:])
            self.n_batch += 1
            
    def batch_forward_propagation(self, batch, i=0):
        if i == len(self.weights)-1:
            #Last Layers
            self.Z[i] = self.weights[i] @ self.A[i]
            self.A[i+1] = self.SoftMax(self.Z[i] + self.biases[i])
            return
        if i == 0:
            self.Z[0] = self.weights[0] @ self.batches[batch]
        else:
            self.Z[i] = self.weights[i] @ self.A[i]
        self.A[i+1] = self.activate(self.activation_functions[i], self.Z[i] + self.biases[i])
        self.batch_forward_propagation(batch, i+1)
    
    def evaluate_forward_propagation(self, i=0):
        if i == len(self.weights)-1:
            #Last Layers
            self.Z[i] = self.weights[i] @ self.A[i]
            self.A[i+1] = self.SoftMax(self.Z[i] + self.biases[i])
            return
        self.Z[i] = self.weights[i] @ self.A[i]
        self.A[i+1] = self.activate(self.activation_functions[i], self.Z[i] + self.biases[i])
        self.evaluate_forward_propagation(i+1)

    def backward_propagation(self, batch, i):
        if i==0:
            dW = self.dZ[0] @ self.batches[batch].T
        else:
            dW = self.dZ[i] @ self.A[i].T
        dW = dW / (dW**2).sum()**0.5
        self.weights[i] -= self.alpha * dW

        db = 1/self.batch_size * np.sum(self.dZ[i])
        self.biases[i]  -= self.alpha * db

        if i == 0:
            return
        self.dZ[i-1] = self.weights[i].T @ self.dZ[i] * self.activate_deriv(self.activation_functions[i-1] ,self.Z[i-1])
        self.backward_propagation(batch, i-1) 

    def cycleAdjusting(self, batch):
        self.batch_forward_propagation(batch)
        self.dZ[-1] = 1/self.batch_size * (self.A[-1] - self.batch_labels[batch])
        self.backward_propagation(batch, len(self.dZ)-1)
        
    def gradient_descent(self):
        for epoch in range(self.epochs):
            currentbatch = trange(self.n_batch, desc='', leave=True)
            for batch in currentbatch:
                self.cycleAdjusting(batch)
                if batch == self.n_batch - 1:
                    self.evaluate_forward_propagation()
                    predictions = self.get_predictions(self.A[-1])
                    accuracy = self.get_accuracy(predictions, self.y_train)
                    currentbatch.set_description(f'Epoch {epoch+1}/{self.epochs}, accuracy={accuracy*100:.2f}%')
                    currentbatch.refresh()

    def addLayer(self, neurons, activation_function=None):
        if self.status: 
            return
        allowed = ['relu','sigmoid','tanh','identity']
        self.hiddenNeurons.append(neurons)
        if activation_function == None:
            self.status = True
            return
        if activation_function not in allowed:
            print('error_activation function not found')
        else:
            self.activation_functions.append(activation_function)

    def init_params(self):
        self.weights = []
        self.biases = []
        self.weights.append(np.random.rand(self.hiddenNeurons[0] , self.n_in) - 0.5)
        self.biases.append(np.random.rand(self.hiddenNeurons[0], 1) - 0.5)
        for n in range(len(self.hiddenNeurons)):
            self.Z.append(0)
            self.dZ.append(0)
            self.A.append(0)
            if n == len(self.hiddenNeurons) - 1:
                break
            self.weights.append(np.random.rand(self.hiddenNeurons[n+1],self.hiddenNeurons[n]) - 0.5)
            self.biases.append(np.random.rand(self.hiddenNeurons[n+1], 1) - 0.5)
        self.status = True

    def fit(self, x_train, y_train, epochs):
        start = time()
        self.epochs = epochs
        self.x_train = x_train
        self.y_train = np.copy(y_train)
        self.A.append(x_train)
        m, n = x_train.shape
        self.n_in  = m
        self.samples = n
        self.n_out = self.hiddenNeurons[-1]
        self.digitize()
        self.prepare_batch()
        self.init_params()
        self.gradient_descent()
        print(f'Finished in {time() - start} s')

    def predict(self, X):
        self.A[0] = X
        self.evaluate_forward_propagation()
        predictions = self.get_predictions(self.A[-1])
        return self.labelize(predictions)
    
    def describe(self):
        print(f'Batch size: {self.batch_size}')
        print(f'{len(self.hiddenNeurons)-1} hidden layers')
        print(f'<> Input layer, {self.n_in} neurons')
        for i in range(len(self.hiddenNeurons)-1):
            print(f'  +> Hidden layer {i+1}, {self.hiddenNeurons[i]} neurons_{self.activation_functions[i]}')
        print(f'<> Output layer, {self.n_out} neurons_softmax')
