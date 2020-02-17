# reportz

httprunner for unittest

## Feature
- 日志
- 添加图片
- 顺序执行/打乱执行
- 多线程
- 失败重试
- [x] 按日期命名
- 多语言
- 发送邮件
- [x] 按测试类统计
- 统计图
- [x] 执行时间
- 超时时间设置
- [x] 环境信息
- 多次运行结果
- 性能分析
- 不稳定用例
- 标记bug
- 增加稳定性
- 异常解释
- [x] extra信息
- [x] 自定义模板
- email支持格式
- 发送到飞书、钉钉、企业微信，短信（仅summary),Confluence(hook)

```python
test_runner = TestRunner(
        report_file_name='index',
        output_path='report',
        title='一个简单的测试报告',
        description='随意描述',
        thread_count=10,
        thread_start_wait=0,
        tries=5,
        delay=1,
        back_off=2,
        retry=False,
        sequential_execution=True,
        lang='cn'
    )
```
## Install
```
pip install reportz
```

## Simple Use


## File type data type mapping


## Todo
