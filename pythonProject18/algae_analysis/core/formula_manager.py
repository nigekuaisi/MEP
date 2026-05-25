import math
import numpy as np


def mepx(x, outputs):
    """您提供的混合藻类核心公式"""
    prg = [0] * 120
    prg[0] = x[5]
    prg[1] = 0.319034
    prg[2] = prg[0] * prg[0]
    prg[3] = x[4]
    prg[4] = math.pow(prg[1], prg[0])
    prg[5] = prg[0] / prg[3]
    prg[6] = prg[2] + prg[2]
    prg[7] = prg[0] - prg[3]
    prg[8] = x[4]
    prg[9] = prg[4] / prg[6]
    prg[10] = prg[8] / prg[7]
    prg[11] = math.pow(prg[9], prg[5])
    prg[12] = prg[3] * prg[6]
    prg[13] = abs(prg[6])
    prg[14] = math.pow(prg[1], prg[5])
    prg[15] = prg[4] * prg[13]
    prg[16] = x[5]
    prg[17] = prg[14] + prg[9]
    prg[18] = x[5]
    prg[19] = math.pow(prg[0], prg[11])
    prg[20] = x[5]
    prg[21] = math.pow(prg[19], prg[17])
    prg[22] = x[0]
    prg[23] = x[1]
    prg[24] = prg[8] * prg[21]
    prg[25] = 0.501267
    prg[26] = prg[17] - prg[5]
    prg[27] = x[1]
    prg[28] = prg[13] + prg[3]
    prg[29] = x[0]
    prg[30] = prg[27] + prg[18]
    prg[31] = prg[12] / prg[28]
    prg[32] = x[4]
    prg[33] = abs(prg[18])
    prg[34] = x[1]
    prg[35] = x[0]
    prg[36] = x[0]
    prg[37] = 1.11847
    prg[38] = prg[28] * prg[7]
    prg[39] = 0.501267
    prg[40] = prg[16] / prg[19]
    prg[41] = prg[14] / prg[0]
    prg[42] = x[3]
    prg[43] = x[2]
    prg[44] = math.pow(prg[24], prg[37])
    prg[45] = prg[39] * prg[26]
    prg[46] = x[0]
    prg[47] = x[4]
    prg[48] = x[5]
    prg[49] = x[1]
    prg[50] = x[2]
    prg[51] = prg[15] * prg[15]
    prg[52] = prg[41] * prg[41]
    prg[53] = x[5]
    prg[54] = 1.11847
    prg[55] = x[1]
    prg[56] = x[0]
    prg[57] = x[5]
    prg[58] = 1.22647
    prg[59] = x[1]
    prg[60] = x[1]
    prg[61] = x[4]
    prg[62] = x[4]
    prg[63] = 1.11847
    prg[64] = x[4]
    prg[65] = prg[41] / prg[23]
    prg[66] = x[4]
    prg[67] = x[2]
    prg[68] = x[3]
    prg[69] = x[3]
    prg[70] = x[2]
    prg[71] = x[5]
    prg[72] = x[0]
    prg[73] = prg[14] - prg[31]
    prg[74] = x[5]
    prg[75] = x[2]
    prg[76] = x[1]
    prg[77] = x[0]
    prg[78] = x[5]
    prg[79] = x[5]
    prg[80] = x[4]
    prg[81] = math.pow(prg[50], prg[32])
    prg[82] = math.sqrt(prg[65])
    prg[83] = x[1]
    prg[84] = x[3]
    prg[85] = x[2]
    prg[86] = prg[78] * prg[78]
    prg[87] = 0.319034
    prg[88] = prg[19] + prg[7]
    prg[89] = 1.22647
    prg[90] = -0.186217
    prg[91] = prg[45] / prg[63]
    prg[92] = prg[52] * prg[52]
    prg[93] = x[2]
    prg[94] = x[4]
    prg[95] = prg[68] / prg[92]
    prg[96] = x[4]
    prg[97] = prg[60] - prg[74]
    prg[98] = x[4]
    prg[99] = x[4]
    prg[100] = x[0]
    prg[101] = 0.501267
    prg[102] = x[4]
    prg[103] = prg[44] * prg[92]
    prg[104] = x[2]
    prg[105] = x[0]
    prg[106] = x[4]
    prg[107] = x[3]
    prg[108] = x[5]
    prg[109] = prg[88] / prg[31]
    prg[110] = prg[54] / prg[78]
    prg[111] = prg[109] / prg[78]
    prg[112] = abs(prg[94])
    prg[113] = x[0]
    prg[114] = x[5]
    prg[115] = x[3]
    prg[116] = x[5]
    prg[117] = prg[4] * prg[4]
    prg[118] = x[5]
    prg[119] = abs(prg[72])
    outputs[0] = prg[109]  # 微拟球藻
    outputs[1] = prg[26]  # 链球藻


class AlgaeFormulaManager:
    @staticmethod
    def formula_nannochloropsis(A430, A480, A680, A730, Ratio_680_730, Ratio_430_680):
        x = [A430, A480, A680, A730, Ratio_680_730, Ratio_430_680]
        try:
            prg = [0.0] * 50
            prg[0] = x[0]
            prg[1] = x[5]
            prg[2] = 5.14044
            prg[3] = x[3]
            prg[4] = prg[3] / prg[0]
            prg[5] = math.sqrt(prg[1])
            prg[6] = math.log(prg[4])
            prg[7] = x[5]
            prg[8] = x[5]
            prg[9] = prg[1] * prg[2]
            prg[10] = prg[9] - prg[2]
            prg[11] = x[2]
            prg[12] = math.log2(prg[2])
            prg[13] = prg[2] / prg[5]
            prg[14] = x[2]
            prg[15] = x[0]
            prg[16] = prg[10] if prg[13] < prg[2] else prg[9]
            prg[17] = prg[5] + prg[6]
            prg[18] = x[1]
            prg[19] = prg[0] if prg[10] < 0 else prg[1]
            prg[20] = prg[16] / prg[17]
            prg[21] = 2.67593
            prg[22] = x[1]
            prg[23] = prg[11] if prg[3] < 0 else prg[16]
            prg[24] = math.pow(prg[11], prg[10])
            prg[25] = math.exp(prg[10])
            prg[26] = math.log2(prg[15])
            prg[27] = math.sqrt(prg[13])
            prg[28] = math.log10(prg[5])
            prg[29] = 2.67593
            prg[30] = math.pow(10, prg[6])
            prg[31] = x[0]
            prg[32] = x[5]
            prg[33] = prg[28] / prg[20]
            prg[34] = x[0]
            prg[35] = prg[8] - prg[24]
            prg[36] = prg[8] * prg[33]
            prg[37] = prg[17] - prg[33]
            prg[38] = prg[33] if prg[20] < prg[1] else prg[4]
            prg[39] = x[3]
            prg[40] = x[4]
            prg[41] = prg[36] if prg[20] < 0 else prg[37]
            prg[42] = x[4]
            prg[43] = -9.54044
            prg[44] = x[4]
            prg[45] = x[1]
            prg[46] = x[0]
            prg[47] = 2.67593
            prg[48] = -9.54044
            prg[49] = math.sqrt(prg[14])
            raw_output = prg[41]
            density = abs(raw_output)
            return AlgaeFormulaManager._format_density(density)
        except Exception as e:
            return np.nan

    @staticmethod
    def formula_chain_algae(A430, A480, A680, A730, Ratio_680_730, Ratio_430_680):
        x0 = A430
        x1 = A480
        x2 = A680
        x3 = A730
        x4 = Ratio_680_730
        x5 = Ratio_430_680
        try:
            prg0 = -0.7723
            prg2 = x0
            prg4 = x5
            prg5 = math.pow(prg4, prg0)
            prg7 = prg5 / prg4
            prg8 = math.log(prg7)
            prg11 = math.sqrt(prg7)
            prg12 = prg11 + prg0
            prg13 = prg2 / prg8
            prg14 = 9.26944
            prg15 = math.exp(prg14)
            prg16 = prg0 if prg15 < prg13 else prg4
            prg20 = math.log(prg2)
            prg22 = prg14 * prg20
            prg25 = prg16 * prg2
            prg28 = prg22 / prg25
            prg41 = prg28 + prg12
            density = abs(prg41)
            return AlgaeFormulaManager._format_density(density)
        except Exception as e:
            return np.nan

    @staticmethod
    def formula_mixed_algae(A430, A480, A680, A730, Ratio_680_730, Ratio_430_680):
        """新增：混合藻类公式，返回两个值"""
        x = [A430, A480, A680, A730, Ratio_680_730, Ratio_430_680]
        outputs = [0.0, 0.0]
        try:
            mepx(x, outputs)
            # outputs[0] = 微拟球藻, outputs[1] = 链球藻
            return (
                AlgaeFormulaManager._format_density(abs(outputs[0])),
                AlgaeFormulaManager._format_density(abs(outputs[1]))
            )
        except Exception as e:
            return np.nan, np.nan

    @staticmethod
    def _format_density(density):
        try:
            return round(density, 6)
        except:
            return np.nan

    @staticmethod
    def get_formula_dict():
        return {
            "微拟球藻 (原始精度版)": AlgaeFormulaManager.formula_nannochloropsis,
            "链球藻 (原始精度版)": AlgaeFormulaManager.formula_chain_algae,
            "混合藻类 (微拟球藻+链球藻)": AlgaeFormulaManager.formula_mixed_algae
        }