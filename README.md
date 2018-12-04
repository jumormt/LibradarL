仅限Linux

$ python3 main.py APK_LIST.TXT THRESHOLD

APK_LIST.TXT为APK文件的列表（每行一个绝对或相对路径）

THRESHOLD为API调用次数阈值，默认为0，如果一个类/包中调用API的次数少于该阈值则不列入统计

如果libdex.so无法使用，在libdex中运行make重新编译一个

结果会保存到result.txt，第一列是包/类的特征值，第二列是出现次数（一个APK中可能出现多次），第三列是出现过的包名/类名