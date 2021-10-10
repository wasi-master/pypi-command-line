# Notes

This page explains certain aspects of the code.

## Imports outside top level

> import statements can be executed just about anywhere. It's often useful to place them inside functions to restrict their visibility and/or reduce initial startup time. Although Python's interpreter is optimized to not import the same module multiple times, repeatedly executing an import statement can seriously affect performance in some circumstances.

From <https://wiki.python.org/moin/PythonSpeed/PerformanceTips#Import_Statement_Overhead>

Because of this, I've added imports in each function that needs them instead of adding them at the top. since the user is only gonna run one single command the imports required for other commands don't need to be imported. Doing this saves around 500ms.
