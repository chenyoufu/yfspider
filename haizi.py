# -*- coding: utf-8 -*-

import jieba
import numpy as np
import matplotlib.pyplot as plt

from os import path
from collections import Counter
from PIL import Image

from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

d = path.dirname(__file__)

with open('haizi.txt', 'r') as poet:
    s = poet.read()

seg_list = [x for x in jieba.cut(s) if len(x) > 1 and x not in [u'一个', u'一只', u'一样', u'一直', u'一种']]

alice_coloring = np.array(Image.open(path.join(d, "haizi.jpg")))

font = "/Library/Fonts/Lantinghei.ttc"
wc = WordCloud(background_color="white", font_path=font, mask=alice_coloring, max_font_size=80, random_state=42, scale=1.5)

# generate word cloud
wc.fit_words(Counter(seg_list).items())

# create coloring from image
image_colors = ImageColorGenerator(alice_coloring)


# show
plt.imshow(wc)
plt.axis("off")
plt.figure()

# recolor wordcloud and show
# we could also give color_func=image_colors directly in the constructor
plt.imshow(wc.recolor(color_func=image_colors))
plt.axis("off")
plt.figure()
plt.imshow(alice_coloring, cmap=plt.cm.gray)
plt.axis("off")
plt.show()

# store to file
wc.to_file(path.join(d, 'haizi.png'))