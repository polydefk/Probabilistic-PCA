import os
import pickle

import numpy as np
from scipy.spatial import distance
from sklearn.datasets import make_circles
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

import MPPCA
import Utils
import ppca_withmissingValues
from KernelPCA import DataTransformation

from PPCA import PPCA

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
mnist_dir = os.path.join(ROOT_DIR, 'data/MNIST/')
toba_dir = os.path.join(ROOT_DIR, 'data/Toba')


class datasets(object):
    def __init__(self):
        pass

    def build_A_toy_dataset(self, N, num_points):

        """
            Generate random data from a N dimensional multivariate distribution
        """
        self.N = N  # number of dimensions
        self.num_points = num_points  # number of data points for each distribution
        self.stdError = 0.1  # sigma value error

        Mean = np.random.randint(10, size=N)
        # sample uniform random variable
        X = np.hstack((np.random.uniform(0, 1, N), np.random.uniform(0, 1, N)))
        X = X[:, np.newaxis]
        X = np.reshape(X, (N, 2))
        A = np.zeros((N, N))
        for i in range(N):
            for j in range(N):
                Pr = (1 / np.sqrt(2 * np.pi)) * np.exp((-1 / (2 * self.stdError)) * distance.euclidean(X[i], X[j]))
                uniform = np.random.uniform(0, 1, 1)  # draw one smaple from the uniform variable
                if (Pr >= uniform):  # If the value is greater than the sample
                    A[i, j] = 1  # we put an edje
                else:  # if the value of Pr is less we put a zero
                    A[i, j] = 0

        Precision = np.zeros((N, N))
        # based on the random adjecency matrix we make a random precision matrix with the edges replaced by 0.245
        for i in range(N):
            for j in range(i + 1):
                if (j == i):
                    Precision[i, j] = 1
                else:
                    if (A[i, j] == 1):
                        Precision[i, j] = 0.245
                        Precision[j, i] = 0.245

        Covariance = np.linalg.inv(Precision)  # covariance is the inverse of the precision

        data = np.random.multivariate_normal(Mean, Covariance,
                                             self.num_points)  # generate the data based on mean and covariance
        X_train, X_test, = train_test_split(data, test_size=0.2)

        return X_train, X_test

    def load_CIFAR10(self, path):
        """

        Load CIFAR10

        link ~ http://www.cs.toronto.edu/~kriz/cifar.html

        Data Description of 5 batch files.

        Each of the batch files contains a dictionary with the following elements:
        data -- a 10000x3072 numpy array of uint8s. Each row of the array stores a 32x32 colour image.
        The first 1024 entries contain the red channel values, the next 1024 the green, and the final 1024 the blue.
        The image is stored in row-major order, so that the first 32 entries of the array are the red channel values
        of the first row of the image.
        labels -- a list of 10000 numbers in the range 0-9. The number at index i indicates the label of the ith
        image in the array data.

        The dataset contains another file, called batches.meta. It too contains a Python dictionary object. I
        t has the following entries:
        label_names -- a 10-element list which gives meaningful names to the numeric labels in the labels array described above.
        For example, label_names[0] == "airplane", label_names[1] == "automobile", etc.
        
        """

        def _load_batch(filename):
            with open(filename, 'rb') as f:
                datadict = pickle.load(f, encoding='latin1')
                X = datadict['data']
                Y = datadict['labels']
                X = X.reshape(10000, 3, 32, 32).transpose(0, 2, 3, 1).astype(
                    "float")  # make the last column the color channel
                Y = np.array(Y)
                return X, Y

        x_train = []
        y_train = []
        for batch in range(1, 6):
            print("=====>Loading Batch file: data_batch_{}<=====".format(batch))

            batch_filename = os.path.join(path, 'data_batch_{}'.format(batch))
            # print(batch_filename)
            X, Y = _load_batch(batch_filename)
            x_train.append(X)
            y_train.append(Y)

        X_train = np.concatenate(x_train)
        y_train = np.concatenate(y_train)

        print("-----------------------------------------")
        print("           CIFAR10 is Loaded")
        print("-----------------------------------------")

        X_test, y_test = _load_batch(os.path.join(path, 'test_batch'))

        return X_train, y_train, X_test, y_test

    def load_MNIST(self, path):
        print("Loading MNIST...")
        """
            Load CIFAR10

            link ~ http://yann.lecun.com/exdb/mnist/

            Data Description:
            
            The data is stored in a very simple file format designed for storing vectors and multidimensional matrices.
            General info on this format is given at the end of this page, but you don't need to read that to use the data files.
            All the integers in the files are stored in the MSB first (high endian) format used by most non-Intel processors.
            Users of Intel processors and other low-endian machines must flip the bytes of the header.

            There are 4 files:

            train-images-idx3-ubyte: training set images
            train-labels-idx1-ubyte: training set labels
            t10k-images-idx3-ubyte:  test set images
            t10k-labels-idx1-ubyte:  test set labels

        """

        def _load_filename(prefix, path):
            intType = np.dtype('int32').newbyteorder('>')
            nMetaDataBytes = 4 * intType.itemsize

            data = np.fromfile(path + "/" + prefix + '-images-idx3-ubyte', dtype='ubyte')
            magicBytes, nImages, width, height = np.frombuffer(data[:nMetaDataBytes].tobytes(), intType)
            data = data[nMetaDataBytes:].astype(dtype='float32').reshape([nImages, width, height])

            labels = np.fromfile(path + "/" + prefix + '-labels-idx1-ubyte',
                                 dtype='ubyte')[2 * intType.itemsize:]

            return data, labels

        trainingImages, trainingLabels = _load_filename("train", path)
        testImages, testLabels = _load_filename("t10k", path)
        print("-----------------------------------------")
        print("           MNIST is Loaded")
        print("-----------------------------------------")
        return trainingImages, trainingLabels, testImages, testLabels

    def load_Toba(self, path):
        print("Loading Tobamovirus dataset..")
        filename = os.path.join(path, 'virus.txt')

        data = read_file(filename)

        print("-----------------------------------------")
        print("           Tobamovirus is Loaded")
        print("-----------------------------------------")
        return data


def dataset_cross(N, d, p):
    """
    N : number of desired points
    d : space dimension
    p : proportion of the 1st branch of the cross (0<p<1)

    X : dataset
    v1, v2 : directions of the branches
    center : center of the cross
    """

    t = np.random.randn(N, 1)
    v1 = np.random.randn(1, d)
    v2 = 1.5 * np.random.randn(1, d)
    center = 5. * np.random.randn(1, d)

    separation = int(round(N * p))

    X = np.zeros((N, d))
    X[:separation, :] = v1 * t[:separation, :]
    X[separation:, :] = v2 * t[separation:, :]
    X += 0.1 * np.random.randn(N, d)
    X += center

    return X, v1, v2, center


# Load MNIST ONLINE. Sometimes gets it gets you http error.
# def _load_mnist():
#     '''
#     Load the digits dataset
#     fetch_mldata ... dataname is on mldata.org, data_home
#     load 10 classes, from 0 to 9
#     '''
#     mnist = datasets.fetch_mldata('MNIST original')
#     n_train = 60000  # The size of training set
#     # Split dataset into training set (60000) and testing set (10000)
#     data_train = mnist.data[:n_train]
#     target_train = mnist.target[:n_train]
#     data_test = mnist.data[n_train:]
#     target_test = mnist.target[n_train:]
#     return (data_train.astype(np.float32), target_train.astype(np.float32),
#             data_test.astype(np.float32), target_test.astype(np.float32))


def plot(data):
    print(data.shape)
    for i in range(data.shape[0]):
        plt.text(data[i, 0], data[i, 1], str(i + 10))

    # min0 = np.min(train[:, 0])
    # min1 = np.min(train[:, 0])
    # max0 = np.max(train[:, 1])
    # max1 = np.max(train[:, 1])

    # plt.axis((min0, max0, min1, max1))

    plt.axis((-10, 15, -10, 15))

    plt.show()


def plot_clusters(data, indices_of_data):
    print(data.shape)
    for i in range(data.shape[0]):
        plt.text(data[i, 0], data[i, 1], indices_of_data[i] + 10)

    # min0 = np.min(train[:, 0])
    # min1 = np.min(train[:, 0])
    # max0 = np.max(train[:, 1])
    # max1 = np.max(train[:, 1])

    # plt.axis((min0, max0, min1, max1))
    plt.axis((-5, 6, -5, 6))

    plt.show()


def plot_colored_clusters(data, assignments):
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title('Three component PPCA mixture model', fontsize=20)
    targets = [0, 1, 2]
    colors = ['r', 'g', 'b']
    for target, color in zip(targets, colors):
        indicesToKeep = np.where(assignments == target)[0]

        ax.scatter(data[indicesToKeep, 0]
                   , data[indicesToKeep, 1]
                   , c=color
                   , s=50)

    for i in range(data.shape[0]):
        plt.text(data[i, 0], data[i, 1], str(i + 10))

    plt.axis((-5, 6, -5, 6))

    ax.legend(['Model_0', 'Model_1', 'Model_2'])
    ax.grid()
    plt.show()


def read_file(name):
    data = []
    i = 0
    with open(name, "r") as f:
        for line in f:
            data.append([])
            data[i] = [float(n) for n in line.split()]
            i += 1

    data = np.array(data)
    return data


def run_Mixture(data):
    num_clusters = 3
    num_dims = 2
    niter = 100

    [pi, mu, W, sigma2, clusters] = MPPCA.initialization_kmeans(X=data, p=num_clusters, q=num_dims)
    [pi, mu, W, sigma2, R, L, sigma2hist] = MPPCA.mppca_gem(data, pi, mu, W, sigma2, niter)
    predictions = MPPCA.mppca_predict(data, pi, mu, W, sigma2)

    cluster_assignments = predictions.argmax(axis=1)
    return cluster_assignments


def run_ppca(data, isMissingData=False):
    # sk learn pca

    # pca = PCA(n_components=2)
    # train_transformed = pca.fit_transform(data)

    # our pca does not work
    # ppca = PPCA(num_components=2,max_iterations=20)
    # ppca.fit(train)
    # train = ppca.transform_data(train)

    if isMissingData:
        data = Utils.get_missing_data_test(data)

    rob_pca = ppca_withmissingValues.ppca_withmissingValues()
    rob_pca.fit(data, d=2)
    train_transformed = rob_pca.transform()

    # data = np.array(data).T
    #
    #
    # train_transformed = ppca__.ppca__().fit_transform(data)
    # train_transformed = np.array(train_transformed).T

    return train_transformed


def plot_circles(data, y, title):
    plt.figure(figsize=(8, 6))
    plt.scatter(data[y == 0, 0], data[y == 0, 1], color='red', alpha=0.5)
    plt.scatter(data[y == 1, 0], data[y == 1, 1], color='blue', alpha=0.5)

    plt.title(title)
    plt.text(-0.18, 0.18, 'gamma = 15', fontsize=12)
    plt.xlabel('PC1')
    plt.ylabel('PC2')
    plt.show()


if __name__ == '__main__':
    from sklearn import datasets

    iris = datasets.load_iris()
    data = iris.data
    y = iris.target

    plot_circles(data, y, " iris original data")


    data, y = make_circles(n_samples=400, factor=.3, noise=.05)

    plot_circles(data, y, " original data")

    kpca_poly = DataTransformation(kernel="poly", gamma=4)

    kpca_poly_transformed = kpca_poly.transform_data(data)

    kpca_rbf = DataTransformation(kernel="rbf", gamma=4)

    kpca_rbf_transformed = kpca_rbf.transform_data(data)

    data_transformed = run_ppca(data=data, isMissingData=False)

    pca = PCA(n_components=2)
    train_transformed = pca.fit_transform(data)
    train_back = pca.inverse_transform(train_transformed)

    plot_circles(kpca_poly_transformed, y, " k pca  poly transformed data")
    plot_circles(kpca_rbf_transformed, y, " k pca  rbftransformed data")
    plot_circles(data_transformed, y, " probabilsitic pca transformed data")

    plot_circles(train_transformed, y, " pca transformed data")

    plot_circles(train_back, y, " pca inversed transformed data")

    # train = datasets().load_Toba(toba_dir)
    #
    # print(train.shape)
    #
    # assignments = run_Mixture(train)
    #
    # indicesofClass0 = np.where(assignments == 0)[0]
    # indicesofClass1 = np.where(assignments == 1)[0]
    # indicesofClass2 = np.where(assignments == 2)[0]
    #
    # train_transformed = run_ppca(data=train, isMissingData=False)
    # plot(train_transformed)
    #
    # plot_colored_clusters(train_transformed, assignments)
    #
    # plot_clusters(train_transformed[indicesofClass0], indicesofClass0)
    # plot_clusters(train_transformed[indicesofClass1], indicesofClass1)
    # plot_clusters(train_transformed[indicesofClass2], indicesofClass2)
