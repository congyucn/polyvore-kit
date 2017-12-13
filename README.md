# polyvore-kit
Development kit for Polyvore Dataset

# 数据集说明
polyvore数据集放在 `/data/poyvore/processed`中.
### 图像
其中, 图像数据放在`images`中,
```
/data/polyvore/processed/images
    |- items/
      |- top/ # images for top item
      |- bottom/ # images for bottom item
      |- shoe/ # images for shoe item
    |- sets/ # images for set
```

## fashion sets 和 fashion items
关于fashion sets 和 fashion items的信息保存在文件夹`pickles`下.
```
/data/polyvore/processed/pickles
    |- fashion_sets.pickle
    |- fashion_items.pickle
```
### 读入数据
通过调用`load_pickle`函数来读取这两个数据:
```python
from utils.data_utils import load_pkl
fashion_sets, fashion_items = load_pkl('/data/polyvore/processed/pickles')
```
### fashion items

其中`fashion_items`以字典类型保存了所有item的信息, 字典的关键字是图像的名字:
```
fashion_items = {image name: item_info}
item_info =
    { 'class': item class in {'top', 'bottom', 'shoe'},
      'name' : the name of item
      'categories' : a list of possible categories,
      'price' : the price of this item,
      'text': the description for this item}
```
例如, 对于图像
```
image_name = 'fc29eece94d29722603d0c13b24d8f9ed9068496.jpg
```
通过`fashion_items[image_name]` 得到该物品的其他描述:
```
{'categories': [u'Shop', u'Tank Tops', u'Calypso St. Barth tops', u'Tops'],
 'class': 'top',
 'name': u'Calypso St. Barth Trista Cotton Tank',
 'price': u'$45',
 'text': u'Every mademoiselle should covet this seamless camisole
          for layering ease.  Stretchy spaghetti strap tank is
          available in an array of neutral shades.  Hitting below
          the hip, this essential piece requires no consistent
          tugging or belly peeking.  The perfect companion for our
          array of semi-sheer feminine tops without compromising
          style.'
}
```


### fashion sets
fashion sets 保存所有用户的set信息. 每一个set的信息有
```
one_set['url']: set url
one_set['image']: set image name
one_set['items']: fashion items indicting by item image name
    one_set['items'][n]: item image name for n-th category
```
例如第0个用户的第0个set是`fashion_sets[0][0]`:
```
{'image': u'e0cf7594f0907c86e067a0a8d451daf32beea738.jpg',
 'items': [
  [u'5950700e921b3779138f4323b3aa9eee300005c6.jpg'], # top
  [u'7ef8d7a7c9534771392b1d8b0bc3b907b1c2562c.jpg',
   u'adb49d364183aa9c66e57ce4a33fa664041ab8ed.jpg'], # bottom
  [u'7817b8ec0457832936c04e30a6e4cf307028255f.jpg'] # shoe
  ],
 'url': u'http://www.polyvore.com/style_steal_cara_delevingne/set?id=177034953'}
```
`fashion_sets` 只是保存了一个初步的信息. 处理之后的positive set保存在文本中.

> 经过处理之后的fashion sets以tuple形式保存在 tuples 文件夹中

## image list 和 tuples
在文件夹`image_list`中保存了每一个类item的图像
```
/data/polyvore/processed/image_list
  |- image_list_top
  |- image_list_bottom
  |- image_list_shoe

/data/polyvore/processed/tuples
  |- tuples_train_posi
  |- tuples_train_nega
  |- tuples_val_posi
  |- tuples_val_nega
  |- tuples_test_posi
  |- tuples_test_nega
```

`tuples` 文件夹保存了训练数据, 每一个样本保存成`(user id, top id, bottom id, shoe id)` 的形式.
例如`(0,1,3,5)`代表了第0个用户的一组套装,这组的套装的top来自`image_list_top`中第1个物品, `image_list_bottom`中的第3个以及`image_list_shoe`中的第5个.


### image list 和 tuples 的读取

```python
from utils.data_utils import DataFile
datafile = DataFile('/data/polyvore/processed/image_list',
                    '/data/polyvore/processed/tuples')
imge_list = datafile.image_list
positive_tuples, negative_tuples = datafile.get_tuples('train')
```

#### image list
`datafile.image_list`返回读取的image list, 其中
- `datafile.image_list[0]`对应读取的是`image_list_top`
- `datafile.image_list[1]`对应读取的是`image_list_bottom`
- `datafile.image_list[2]`对应读取的是`image_list_shoe`

#### tuples
`datafile.get_tuples`返回两个`np.array`数组．
```
positive_tuples, negative_tuples = datafile.get_tuples('train') # train
positive_tuples, negative_tuples = datafile.get_tuples('val') # val
positive_tuples, negative_tuples = datafile.get_tuples('test') # test
```
其中`positive_tuples`和`negative_tuples`分别保存了正样本和负样本，其中正样本是用户自己创建的，负样本是随机生成的．
