from energyOptimal.monitor import monitorProcess
from energyOptimal.monitor import cpuFreq
from energyOptimal.sensors.ipmi import IPMI
from energyOptimal.sensors.rapl import RAPL

args_black=\
[\
["__nt__","in_5_10.txt","output.txt"],\
["__nt__","in_6_10.txt","output.txt"],\
["__nt__","in_7_10.txt","output.txt"],\
["__nt__","in_8_10.txt","output.txt"],\
["__nt__","in_9_10.txt","output.txt"]
]
args_canneal=\
[\
["__nt__","15000","2000","2500000.nets","128"],\
["__nt__","15000","2000","2500000.nets","256"],\
["__nt__","15000","2000","2500000.nets","384"],\
["__nt__","15000","2000","2500000.nets","512"],\
["__nt__","15000","2000","2500000.nets","640"]
]
args_dedup=\
[\
["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_05.iso","-o","output.dat.ddp"],\
["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_06.iso","-o","output.dat.ddp"],\
["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_07.iso","-o","output.dat.ddp"],\
["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_08.iso","-o","output.dat.ddp"],\
["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_09.iso","-o","output.dat.ddp"]
]
args_ferret=\
[\
["corel_5","lsh","queries_5","10","20","__nt__","output.txt"],\
["corel_6","lsh","queries_6","10","20","__nt__","output.txt"],\
["corel_7","lsh","queries_7","10","20","__nt__","output.txt"],\
["corel_8","lsh","queries_8","10","20","__nt__","output.txt"],\
["corel_9","lsh","queries_9","10","20","__nt__","output.txt"]
]
args_fluid=\
[\
["__nt__","200","in_500K.fluid","out.fluid"],\
["__nt__","300","in_500K.fluid","out.fluid"],\
["__nt__","400","in_500K.fluid","out.fluid"],\
["__nt__","500","in_500K.fluid","out.fluid"],\
["__nt__","600","in_500K.fluid","out.fluid"]
]
args_freq=\
[\
["webdocs_250k_05.dat","11000"],\
["webdocs_250k_06.dat","11000"],\
["webdocs_250k_07.dat","11000"],\
["webdocs_250k_08.dat","11000"],\
["webdocs_250k_09.dat","11000"]
]
args_rtview=\
[\
["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","346","346"],\
["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","374","374"],\
["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","400","400"],\
["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","424","424"],\
["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","450","450"]
]
args_swap=\
[\
["-ns","32","-sm","2000000","-nt","__nt__"],\
["-ns","32","-sm","3000000","-nt","__nt__"],\
["-ns","32","-sm","4000000","-nt","__nt__"],\
["-ns","32","-sm","5000000","-nt","__nt__"],\
["-ns","32","-sm","6000000","-nt","__nt__"]
]
args_vips=\
[\
["im_benchmark","orion_10800x10800.v","output.v"],\
["im_benchmark","orion_12600x12600.v","output.v"],\
["im_benchmark","orion_14400x14400.v","output.v"],\
["im_benchmark","orion_16200x16200.v","output.v"],\
["im_benchmark","orion_18000x18000.v","output.v"]
]
args_x264=\
[\
["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_306.y4m"],\
["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_357.y4m"],\
["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_408.y4m"],\
["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_459.y4m"],\
["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_512.y4m"]
]
args_xhpl= [['__nt__','7000'],\
    ['__nt__','8000'],\
    ['__nt__','9000'],\
    ['__nt__','10000'],\
    ['__nt__','11000']\
]
args_openmc= [['input1'],\
    ['input2'],\
    ['input3'],\
    ['input4'],\
    ['input5']\
]
args_body=[['sequenceB_1043', '4', '204', '1000', '10', '0', '__nt__'],\
['sequenceB_1043', '4', '408', '1000', '10', '0', '__nt__'],\
['sequenceB_1043', '4', '612', '1000', '10', '0', '__nt__'],\
['sequenceB_1043', '4', '816', '1000', '10', '0', '__nt__'],\
['sequenceB_1043', '4', '1020', '1000', '10', '0', '__nt__']\
]

try:
    cpu= cpuFreq()
    sensor= IPMI(server= "http://localhost:8080", name_="admin", password_="admin")

    programs= [monitorProcess(program_name_= 'apps/openmc_/openmc',             sensor= sensor),
               monitorProcess(program_name_= 'apps/xhpl_/xhpl',                 sensor= sensor),
               monitorProcess(program_name_= 'apps/canneal_/canneal',           sensor= sensor),
               monitorProcess(program_name_= 'apps/dedup_/dedup',               sensor= sensor),
               monitorProcess(program_name_= 'apps/ferret_/ferret',             sensor= sensor),
               monitorProcess(program_name_= 'apps/x264_/x264',                 sensor= sensor),
               monitorProcess(program_name_= 'apps/vips_/vips',                 sensor= sensor),
               monitorProcess(program_name_= 'apps/blackscholes_/blackscholes', sensor= sensor),
               monitorProcess(program_name_= 'apps/fluidanimate_/fluidanimate', sensor= sensor),
               monitorProcess(program_name_= 'apps/swaptions_/swaptions',       sensor= sensor),
               monitorProcess(program_name_= 'apps/rtview_/rtview',             sensor= sensor),
               monitorProcess(program_name_= 'apps/bodytrack_/bodytrack',       sensor= sensor),
               monitorProcess(program_name_= 'apps/freqmine_/freqmine',         sensor= sensor)
    ]

    args= [args_openmc, args_xhpl, args_canneal, args_dedup,
            args_ferret, args_x264, args_vips, args_black, args_fluid, args_swap, args_rtview, args_body, args_freq]

    for p, a in zip(programs,args):
#        if not 'canneal' in p.program_name:
#            continue
        try:
            if 'fluid' in p.program_name:
                thr= [1,2,4,8,16,32]
            else:
                thr= [1]+list(range(2,33,2))
            frs= cpu.get_available_frequencies()[::2]
            p.run_dvfs(list_threads= thr, list_frequencies=frs, list_args= a, idle_time= 30,
                        verbose=2, save_name='data/dvfs/{}_completo_5.pkl'.format(p.program_name))
        except Exception as e:
            print(e)
except:
    cpu.reset()