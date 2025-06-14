import argparse
import json
import os
import shutil

import ast_parse_ttml_js
from model.mpk import MPK
from loguru import logger

OUTPUT_FOLDER = ""
COMMON_STYLESHEETS = {}


# 根据开始字符串和结束字符串裁剪字符串内容
def get_string_by_seperators(source, begin_str, end_str, begin_index):
    index = source.find(begin_str, begin_index)
    if index == -1:
        return "", -1

    index2 = source.find(end_str, index + len(begin_str))
    if index2 == -1:
        return "", -1

    return source[index + len(begin_str):index2], index2 + len(end_str)


# 创建目录
def md(dir):
    if os.path.exists(dir) is False:
        os.mkdir(dir)


# 删除目录
def rm(dir):
    if os.path.exists(dir) is True:
        shutil.rmtree(dir)


def delete_file(file_path):
    """
    删除指定路径下的文件，支持多层路径。

    参数:
        file_path (str): 要删除的文件路径（例如 output/css/file1.css）

    返回:
        bool: 删除成功返回 True，失败或文件不存在返回 False
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            # logger.info(f"文件 {file_path} 不存在")
            return False

        # 确保路径是文件而非目录
        if not os.path.isfile(file_path):
            # logger.info(f"{file_path} 不是文件")
            return False

        # 删除文件
        os.remove(file_path)
        # logger.info(f"成功删除文件: {file_path}")
        return True

    except PermissionError:
        # logger.info(f"无权限删除文件: {file_path}")
        return False
    except Exception as e:
        # logger.info(f"删除文件 {file_path} 失败: {e}")
        return False


def write_to_file(filename, content, output_dir="output"):
    """
    将内容写入指定文件名的文件中，如果路径不存在则创建目录。

    参数:
        filename (str): 目标文件名（如 file1.css）
        content (str): 要写入的文件内容
        output_dir (str): 输出目录，默认为 "output"
    """
    # 构建完整的文件路径
    file_path = os.path.join(output_dir, filename)

    # 获取目录路径
    directory = os.path.dirname(file_path)

    # 如果目录不存在，创建目录
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    # 写入文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        # logger.info(f"成功写入文件: {file_path}")
    except Exception as e:
        logger.error(f"写入文件 {file_path} 失败: {e}")


def process_ttss(fname):
    """
    处理 CSS_MAP，解析并将内容写入文件。

    参数:
        source (str): 包含 CSS_MAP 的源字符串
        output_dir (str): 输出目录，默认为 "output"
    """
    if os.path.exists(fname) is False:
        return

    f = open(fname, "r", encoding='utf-8')
    source = ''.join(f.readlines())
    f.close()
    # 获取 CSS 文件位置
    buf = get_string_by_seperators(source, "Object.assign(window.CSS_MAP||{},", "),window.$m", 0)
    if buf[1] == -1:
        buf = get_string_by_seperators(source, "window.CSS_MAP=", ",window.$m", 0)
    if buf[1] == -1:
        logger.info("获取 CSS_MAP的TTSS文件 失败，请使用解包后的源文件，格式化后的代码无法解析")
        return
    try:
        # 解析 JSON 字符串
        ttss_list = eval(buf[0])
        if not isinstance(ttss_list, dict):
            pass
        else:
            # 遍历文件名和内容
            for filename in ttss_list:
                content = get_wxss_content(ttss_list[filename])

                logger.info(f"Processing {filename}")
                COMMON_STYLESHEETS[filename] = content
                write_to_file(filename, content, OUTPUT_FOLDER)
    except Exception as e:
        logger.warning(f"处理 CSS_MAP 时发生错误: {e}")
    parseputCssToHead(source, fname)


def parseputCssToHead(source, fname):
    # 处理putCssToHead
    token = ".wxss"
    jsons = source.split("putCssToHead(")
    for j in jsons:
        if fname.endswith("page-frame.js"):
            if token in j:  # page-frame.js的处理方式
                index = j.find('.wxss",', 0)
                if index == -1:
                    continue
                try:
                    buf = eval('[' + j[0:index].replace("undefined", '[]').replace("path", '"path"') + '.ttss"]')
                    filename = buf[1]
                    content = get_wxss_content(buf[0])

                    logger.info(f"Processing {filename}")
                    COMMON_STYLESHEETS[filename] = content
                    write_to_file(filename, content, OUTPUT_FOLDER)
                except Exception as e:
                    logger.info(e)
        else:
            # logger.info("其他文件的处理方式" + fname)
            index = j.find('),",', 0)
            index1 = j.find(');var', 0)
            if index == -1 and index1 == -1:
                continue
            index = index if index1 == -1 else index1
            try:
                buf = eval('[' + j[0:index].replace("undefined", '[]').replace("path", '"path"') + ']')
                delete_file(fname)
                filename = fname.replace("-frame.js", '.ttss').replace(OUTPUT_FOLDER + '/', '')
                content = get_wxss_content(buf[0])

                logger.info(f"Processing {filename}")
                COMMON_STYLESHEETS[filename] = content
                write_to_file(filename, content, OUTPUT_FOLDER)
            except Exception as e:
                logger.info(e)


def get_wxss_content(buf):
    if type(buf).__name__ == "str":
        return buf

    content = ""
    for item in buf:
        if type(item).__name__ == "str":
            content += item
        elif type(item).__name__ == "list":
            op = item[0]
            if op == 0:
                content += str(item[1])  # rpx不处理了，直接加
            elif op == 1:
                pass
            elif op == 2:
                wxss = "@import \"/%s;" % item[1]
                if wxss is None:
                    pass
                else:
                    content += wxss
    return content


def process(flist, func):
    for f in flist:
        func(OUTPUT_FOLDER + f)
        with open(OUTPUT_FOLDER + "/app-config.json", "r", encoding='utf-8') as fs:
            j = json.load(fs)
            if hasattr(j, "subPackages"):
                for sub in j["subPackages"]:
                    func(OUTPUT_FOLDER + "/" + sub["root"] + f)


def processPageTtss():
    """
    解析子目录的ttss文件
    :return:
    """
    with open(OUTPUT_FOLDER + "/app-config.json", "r", encoding='utf-8') as fs:
        j = json.load(fs)
        if "pages" in j:
            for page in j["pages"]:

                file_path = OUTPUT_FOLDER + "/" + page + "-frame.js"
                if os.path.exists(file_path) is False:
                    continue
                f = open(file_path, "r", encoding='utf-8')
                source = ''.join(f.readlines())
                f.close()
                parseputCssToHead(source, file_path)


def processPageJSON():
    """
    解析子目录的ttss文件
    :return:
    """
    jsonFile = "/app-config.json"
    fs = open(OUTPUT_FOLDER + jsonFile, "r", encoding='utf-8')
    j = json.load(fs)
    fs.close()
    if "page" in j:
        page = j["page"]
        for path in page:
            pageObj = page[path]
            filename = path + ".json"
            jsonContent = json.dumps(pageObj['window'], indent=4, ensure_ascii=False)
            logger.info("Processing " + filename)
            write_to_file(filename, jsonContent, OUTPUT_FOLDER)
            # 删除无用service
            delete_file(OUTPUT_FOLDER + "/" + path + "-service.js")
    # 全局配置恢复
    j['window'] = j['global']['window']
    # 需要删除的键
    delKeys = ["global", 'page', 'appId', 'entryPagePath', 'isMicroApp', 'industrySDK', 'usePrivacyCheck']
    for delKey in delKeys:
        if delKey in j:
            del j[delKey]
    # 删除空数据
    for key in list(j.keys()):
        value = j[key]
        if value == [] or value == "" or (isinstance(value, dict) and not value) or value is False:
            del j[key]
    delete_file(OUTPUT_FOLDER + jsonFile)
    delete_file(OUTPUT_FOLDER + "/app-service.js")
    # 写入app.json
    newAppJson = json.dumps(j, indent=4, ensure_ascii=False)
    write_to_file("app.json", newAppJson, OUTPUT_FOLDER)


def process_package(file):
    global OUTPUT_FOLDER
    with open(file, 'rb') as pkgfile:
        mpk = MPK.load(pkgfile)
        for i in mpk.files:
            file = mpk.file(i)
            if file['offset'] != 0:
                if file['name'] == '':
                    file['name'] = 'unknown_%s' % i
                logger.info('Unpacking: %s' % file['name'])
                path_file = '%s/%s' % (OUTPUT_FOLDER, file['name'])
                dir_file, _ = os.path.split(path_file)
                os.makedirs(dir_file, exist_ok=True)
                with open(path_file, 'wb') as io_file:
                    io_file.write(mpk.data(i))
# OUT_PATH = "js/038d897.ttpkg.js_unpack/"

def processTtmlByAst(file_path):
    """

    :return:
    """
    f = open(OUTPUT_FOLDER + file_path, "r", encoding='utf-8')
    source = ''.join(f.readlines())
    f.close()
    pageJs = source.split("window.$m_")[1:]
    pageList = {}
    for page in pageJs:
        begin_str = "window.app[\""
        end_str = "\"]"
        pageTag = page[0:page.find("=createCommonjsModule")]  # 裁剪出模块名称
        if page.find(begin_str) != -1:
            file_name_begin = page.find(begin_str) + len(begin_str)
            file_name_end = page.find(end_str, file_name_begin)
            filename = page[file_name_begin:file_name_end]
            # 存入页面列表，方便后续解析其他模块导入时使用
            pageList[pageTag] = filename
            logger.info(f"Decompiling {filename}.ttml")
            astJs = page[0:file_name_begin - len(begin_str) - 1]
            ast_parse_ttml_js.run(astJs, pageList, OUTPUT_FOLDER + "/" + filename + ".ttml")


def end():
    """
    最后删除不用的文件
    :return:
    """
    delete_files_list = ["data.js", "page-frame.js", "preload-modules.json", "script.js", ]
    for file_name in delete_files_list:
        delete_file(OUTPUT_FOLDER + "/" + file_name)


def main(output_folder, input_file):
    """
    主函数，执行解包和反编译流程
    参数:
        output_folder: 输出文件夹路径
        input_file: 输入的小程序包文件路径
        file: 要处理的全局页面文件路径
    """
    global OUTPUT_FOLDER
    file = '/page-frame.js'
    OUTPUT_FOLDER = output_folder  # 设置全局变量
    # 删除输出文件夹
    # rm(OUTPUT_FOLDER)
    # 创建输出文件夹
    # md(OUTPUT_FOLDER)
    # 开始解包小程序包
    logger.info("Unpacking package...")
    # process_package(input_file)
    # 反编译全局的 ttss 文件
    # process([file], process_ttss)
    # 反编译每个界面的 ttss 文件
    # processPageTtss()
    # 构造 page.json 文件
    # processPageJSON()
    # 通过 AST 反编译 ttml 文件
    processTtmlByAst(file)
    logger.info("Operation completed successfully!")


if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="pkg文件路径")
    parser.add_argument(
        "-i",
        "--input_file",
        type=str,
        required=True,
        help="输入pkg文件 (e.g., 'js/e2670a8.pkg')"
    )
    # 添加简写参数
    parser.add_argument(
        "-o",
        "--output_folder",
        type=str,
        default="output",
        help="输出目录 (默认: 'output')"
    )

    # 解析命令行参数
    args = parser.parse_args()
    # 调用主函数，传入解析的参数
    main(args.output_folder, args.input_file)
