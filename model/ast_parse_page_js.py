import esprima
"""
TODO 该文件为解析页面对应的js文件,大致看了js文件的结构下，格式化一下基本都能看懂逻辑了，写了一半就懒得写了。
"""
# 读取输入的 JavaScript 文件
def read_js_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


# 将提取的内容写入输出文件
def write_js_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)


# 提取 define 函数第二个参数的函数体
def extract_function_body(js_code):
    try:
        # 解析 JavaScript 代码为 AST，显式启用 loc 和 range
        ast = esprima.parseScript(js_code, {'loc': True, 'range': True})

        # 遍历 AST，查找 define 函数调用
        for node in ast.body:
            if node.type == 'ExpressionStatement' and node.expression.type == 'CallExpression':
                callee = node.expression.callee
                if callee.type == 'Identifier' and callee.name == 'define':
                    # 确保 define 函数有至少两个参数
                    if len(node.expression.arguments) >= 2:
                        second_arg = node.expression.arguments[1]
                        # 检查第二个参数是否为函数表达式
                        if second_arg.type == 'FunctionExpression':
                            # 检查 body 和 loc 是否存在
                            if hasattr(second_arg, 'body') and hasattr(second_arg.body, 'loc'):
                                # 检查 loc 的 start 和 end 是否有效
                                if second_arg.body.loc and second_arg.body.loc.start and second_arg.body.loc.end:
                                    # 使用 range 提取函数体（更可靠）
                                    start_offset = second_arg.body.range[0]
                                    end_offset = second_arg.body.range[1]
                                    function_body = js_code[start_offset+1:end_offset-1]
                                    return function_body.strip()
                                else:
                                    return "错误：函数体的位置信息（loc）不完整"
                            else:
                                return "错误：函数体或位置信息（loc）缺失"
        return "未找到 define 函数或其第二个参数不是函数"
    except esprima.Error as e:
        return f"解析 JavaScript 代码失败：{str(e)}"


# 主函数
def main(input_file='js_code.js', output_file='out.js'):
    try:
        # 读取输入文件
        js_code = read_js_file(input_file)
        # 提取函数体
        function_body = extract_function_body(js_code)
        # 写入输出文件
        write_js_file(output_file, function_body)
        print(f"成功提取函数体并保存到 {output_file}")
    except FileNotFoundError:
        print(f"错误：找不到文件 {input_file}")
    except Exception as e:
        print(f"处理过程中发生错误：{str(e)}")


if __name__ == "__main__":
    main()