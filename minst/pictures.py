from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
from werkzeug.utils import secure_filename
import os
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
from PIL import Image
import time

from datetime import timedelta

# 设置允许的文件格式
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'JPG', 'PNG', 'bmp'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


app = Flask(__name__)
# 设置静态文件缓存过期时间
app.send_file_max_age_default = timedelta(seconds=1)


# @app.route('/upload', methods=['POST', 'GET'])
@app.route('/upload', methods=['POST', 'GET'])  # 添加路由
def upload():
    if request.method == 'POST':
        f = request.files['file']

        if not (f and allowed_file(f.filename)):
            return jsonify({"error": 1001, "msg": "请检查上传的图片类型，仅限于png、PNG、jpg、JPG、bmp"})


        im = Image.open(f)
        data = list(im.getdata())
        result = [(255 - x) * 1.0 / 255.0 for x in data]
        print(result)

        # 为输入图像和目标输出类别创建节点
        x = tf.placeholder("float", shape=[None, 784])  # 训练所需数据  占位符

        # *************** 构建多层卷积网络 *************** #
        def weight_variable(shape):
            initial = tf.truncated_normal(shape, stddev=0.1)  # 取随机值，符合均值为0，标准差stddev为0.1
            return tf.Variable(initial)

        def bias_variable(shape):
            initial = tf.constant(0.1, shape=shape)
            return tf.Variable(initial)

        def conv2d(x, W):
            return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

        def max_pool_2x2(x):
            return tf.nn.max_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')

        x_image = tf.reshape(x, [-1, 28, 28, 1])  # -1表示任意数量的样本数,大小为28x28，深度为1的张量

        W_conv1 = weight_variable([5, 5, 1, 32])  # 卷积在每个5x5的patch中算出32个特征。
        b_conv1 = bias_variable([32])
        h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)
        h_pool1 = max_pool_2x2(h_conv1)

        W_conv2 = weight_variable([5, 5, 32, 64])
        b_conv2 = bias_variable([64])
        h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)
        h_pool2 = max_pool_2x2(h_conv2)

        W_fc1 = weight_variable([7 * 7 * 64, 1024])
        b_fc1 = bias_variable([1024])
        h_pool2_flat = tf.reshape(h_pool2, [-1, 7 * 7 * 64])
        h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

        # 在输出层之前加入dropout以减少过拟合
        keep_prob = tf.placeholder("float")
        h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

        # 全连接层
        W_fc2 = weight_variable([1024, 10])
        b_fc2 = bias_variable([10])

        # 输出层
        # tf.nn.softmax()将神经网络的输层变成一个概率分布
        y_conv = tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)

        saver = tf.train.Saver()  # 定义saver

        # *************** 开始识别 *************** #
        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())
            saver.restore(sess, "./save/model.ckpt")  # 这里使用了之前保存的模型参数

            prediction = tf.argmax(y_conv, 1)
            predint = prediction.eval(feed_dict={x: [result], keep_prob: 1.0}, session=sess)

            print("recognize result: %d" % predint[0])



        return render_template('upload_ok.html',userinput=predint[0], val1=time.time())

    return render_template('upload.html')


if __name__ == '__main__':
    # app.debug = True
    app.run(host='0.0.0.0', port=80 )
