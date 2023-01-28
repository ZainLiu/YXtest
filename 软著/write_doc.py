import os

import docx

def walkFile(file, doc):

    for root, dirs, files in os.walk(file):

        # root 表示当前正在访问的文件夹路径

        # dirs 表示该文件夹下的子目录名list

        # files 表示该文件夹下的文件list

        # 遍历文件

        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                with open(os.path.join(root, f), "r", encoding="utf8") as f:
                    data = f.read()
                    doc.add_paragraph(data)


        # 遍历所有的文件夹

        for d in dirs:

            walkFile(d, doc)

doc = docx.Document()
walkFile("./module", doc)
doc.save("ops软著代码.docx")




