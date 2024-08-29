# if __name__ == "__main__":
#     from devtools import pprint

#     from chromatopy.units import mM

#     dir_path = "/Users/max/Documents/jan-niklas/MjNK/guanosine_std"
#     file_path = (
#         "/Users/max/Documents/jan-niklas/MjNK/Standards/Adenosine Stadards_ 0.5 mM.txt"
#     )

#     data_path = "/Users/max/Documents/jan-niklas/MjNK"

#     data_ana = ChromAnalyzer.read_chromeleon(data_path)

#     ana = ChromAnalyzer.read_chromeleon(dir_path)
#     del ana.measurements[0]

#     ana.find_peaks()

#     ana.add_molecule(
#         ld_id="www.mol.com",
#         id="s0",
#         name="Guanosine",
#         retention_time=6.03,
#     )

#     print(ana.molecules)

#     # find and fit peaks

#     # scatterplot as multiplot for each measurement

#     # for meas in ana.measurements[1:]:
#     #     for chrom in meas.chromatograms:
#     #         chrom.fit()

#     # from matplotlib import pyplot as plt

#     # plt.plot(
#     #     ana.measurements[0].chromatograms[0].times,
#     #     ana.measurements[0].chromatograms[0].signals,
#     # )
#     # plt.plot(
#     #     ana.measurements[1].chromatograms[0].times,
#     #     ana.measurements[1].chromatograms[0].signals,
#     # )
#     # plt.plot(
#     #     ana.measurements[2].chromatograms[0].times,
#     #     ana.measurements[2].chromatograms[0].signals,
#     # )
#     # plt.show()

#     from chromatopy.units import C

#     stan = ana.add_standard(
#         ana.molecules[0], 7.4, 37, C, [0.5, 1, 1.5, 2, 2.5], mM, visualize=True
#     )
#     pprint(stan)
