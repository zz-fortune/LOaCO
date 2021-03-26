# encoding: utf-8

"""
@File    :   LP.py
@Time    :   2021/03/26 21:52:52
@Author  :   zheng heng 
@Version :   1.0
@Contact :   heng@hit.edu.cn
@Desc    :   线性规划-单纯形算法
"""

import numpy as np

np.set_printoptions(precision=4, suppress=True, threshold=np.inf)


def get_loose_matrix(matrix):
    """线性规划转化为松弛形式"""
    row, col = matrix.shape
    loose_matrix = np.zeros((row, row + col))
    for i, _ in enumerate(loose_matrix):
        loose_matrix[i, 0: col] = matrix[i]
        loose_matrix[i, col + i] = 1.0  # 对角线
    return loose_matrix


def join_matrix(a, b, c):
    """松弛形式的系数矩阵A、约束矩阵B和目标函数矩阵C组合为一个矩阵"""
    row, col = a.shape
    s = np.zeros((row + 1, col + 1))

    # 右下角是松弛系数矩阵A
    s[1:, 1:] = a

    # 左下角是约束条件值矩阵B
    s[1:, 0] = b  

    # 右上角是目标函数矩阵C
    s[0, 1: len(c) + 1] = c  
    return s


def pivot_matrix(matrix, k, j):
    """旋转矩阵—替换替出替入变量的角色位置"""
    # 单独处理替出变量所在行，需要除以替入变量的系数matrix[k][j]
    matrix[k] = matrix[k] / matrix[k][j]

    # 循环除了替出变量所在行之外的所有行
    for i, _ in enumerate(matrix):
        if i != k:
            matrix[i] = matrix[i] - matrix[k] * matrix[i][j]


def get_base_solution(matrix, base_ids):
    """根据旋转后的矩阵，从基本变量数组中得到一组基解"""
    X = [0.0] * (matrix.shape[1])  # 解空间
    for i, _ in enumerate(base_ids):
        X[base_ids[i]] = matrix[i + 1][0]
    return X


def Laux(matrix, base_ids):
    """构造辅助线性规划"""
    l_matrix = np.copy(matrix)

    # 辅助矩阵的最后一列存放x0的系数，初始化为-1
    l_matrix = np.column_stack((l_matrix, [-1] * l_matrix.shape[0]))

    # 辅助线性函数的目标函数为z = x0
    l_matrix[0, :-1] = 0.0
    l_matrix[0, -1] = 1

    # 选择一个b最小的那一行的基本变量作为替出变量
    k = l_matrix[1:, 0].argmin() + 1  

    # 选择x0作为替入变量
    j = l_matrix.shape[1] - 1  

    # 第一次旋转矩阵，使得所有b为正数
    pivot_matrix(l_matrix, k=k, j=j)

    # 维护基本变量索引数组
    base_ids[k - 1] = j  

    # 用单纯形算法求解该辅助线性规划
    l_matrix = simplex(l_matrix, base_ids)
    
    # 如果求解后的辅助线性规划中x0仍然是基本变量，需要再次旋转消去x0
    if l_matrix.shape[1] - 1 in base_ids:

        # 找到矩阵第一行(目标函数)系数不为0的变量作为替入变量
        j = np.where(l_matrix[0, 1:] != 0)[0][0] + 1   

        # 找到x0作为基本变量所在的那一行，将x0作为替出变量
        k = base_ids.index(l_matrix.shape[1] - 1) + 1

        # 旋转矩阵消去基本变量x0
        pivot_matrix(l_matrix, k=k, j=j)   

        # 维护基本变量索引数组
        base_ids[k - 1] = j  
    return l_matrix, base_ids


def resotr_from_Laux(l_matrix, z, base_ids):
    """从辅助函数中恢复原问题的目标函数"""
    # 得到目标函数系数不为0的索引数组(即基本变量索引数组)
    z_ids = np.where(z != 0)[0] - 1  

    # 去掉x0那一列
    restore_matrix = np.copy(l_matrix[:, 0:-1])  

    # 初始化矩阵的第一行为原问题的目标函数向量
    restore_matrix[0] = z  
    for i, base_v in enumerate(base_ids):

        # 如果原问题的基本变量存在新基本变量数组中，说明需要替换消去
        if base_v in z_ids:

            # 消去原目标函数中的基本变量
            restore_matrix[0] -= restore_matrix[0, base_v + 1] * \
                restore_matrix[i + 1]  
    return restore_matrix


def simplex(matrix, base_ids):
    """单纯形算法求解线性规划"""
    matrix = matrix.copy()

    # 如果目标系数向量里有负数，则旋转矩阵
    while matrix[0, 1:].min() < 0:

        # 在目标函数向量里，选取系数为负数的第一个变量索引，作为替入变量
        j = np.where(matrix[0, 1:] < 0)[0][0] + 1

        # 在约束集合里，选取对替入变量约束最紧的约束行，那一行的基本变量作为替出变量
        k = np.array([matrix[i][0] / matrix[i][j] if matrix[i][j] > 0 else 0x7fff for i in
                      range(1, matrix.shape[0])]).argmin() + 1

        # 说明原问题无界
        if matrix[k][j] <= 0:
            print('原问题无界')
            return None, None

         # 旋转替换替入变量和替出变量
        pivot_matrix(matrix, k, j) 

        # 维护当前基本变量索引数组
        base_ids[k - 1] = j - 1  
    return matrix


def solve(a, b, c, equal=None):
    """单纯形算法求解步骤入口"""

    # 转化得到松弛矩阵
    loose_matrix = get_loose_matrix(a)  
    if equal is not None:
        loose_matrix = np.insert(loose_matrix, 0, equal, axis=0)
    
    # 得到ABC的组合矩阵
    matrix = join_matrix(loose_matrix, b, c)  

    # 初始化基本变量的索引数组
    base_ids = list(range(len(c), len(b) + len(c))) 

    # 约束系数矩阵有负数约束，证明没有可行解，需要辅助线性函数
    if matrix[:, 0].min() < 0:
        print('构造求解辅助线性规划函数...')

        # 构造辅助线性规划函数并旋转求解之
        l_matrix, base_ids = Laux(matrix, base_ids)  
        if l_matrix is not None:
            matrix = resotr_from_Laux(

                # 恢复原问题的目标函数
                l_matrix, matrix[0], base_ids)  
        else:
            print('辅助线性函数的原问题没有可行解')
            return None, None, None
    
    # 单纯形算法求解拥有基本可行解的线性规划
    ret_matrix = simplex(matrix, base_ids)  

    # 得到当前最优基本可行解
    X = get_base_solution(ret_matrix, base_ids)  
    if ret_matrix is not None:
        return matrix, ret_matrix, X
    else:
        print('原线性规划问题无界')
        return None, None, None


if __name__ == '__main__':
    equal = None
    a = np.array([[-2, 5, -1], [1, 3, 1]])
    equal = [1, 1, 1] + [0] * a.shape[0]
    b = [7, -10, 12]
    c = [-2, -3, 5]
    matrix, ret_matrix, X = solve(a, b, c, equal=equal)
    print('本次迭代的最优解为：{}'.format(np.round(X[0: len(c)], 4)))
    print('该线性规划的最优值是：{}'.format(np.round(-ret_matrix[0][0], 4)))
