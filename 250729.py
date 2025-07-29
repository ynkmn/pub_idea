from mpi4py import MPI
import subprocess

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

if rank == 0:
    print("Python rank 0: Fortran実行ファイルの起動")
    ret = subprocess.call(["mpiexec", "-n", "4", "./fortran_main.exe"])
    print("Fortranの終了コード：", ret)
