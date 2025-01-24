
Installation
############

Requirements
============

- miniconda
- python3.10 


Installation
============

.. important::

   To use AESP, first install miniconda_:

.. _miniconda: https://docs.anaconda.com/miniconda/install/

如果已经安装好miniconda，就可以安装相应版本的python环境（只能是python3.10版本）并激活。

.. code:: console

   conda create -n aesp python==3.10
   conda activate aesp

To install AESP, 这里有两种可选的方式。\

[1] one can simply type

.. code:: console
   
   pip install aesp

[2] or make a copy of the source code, and then install it manually.

.. code:: console

   git clone https://github.com/stupid-cloud/aesp.git
   cd aesp
   pip install ./

如果你已经安装好aesp，可以尝试输入 ``aesp -v`` 查看当前的版本。You expect to see the following output.

.. code:: console
   
   aesp v2024.8.4

