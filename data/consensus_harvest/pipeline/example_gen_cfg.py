import re
src=open('append_b12.py',encoding='utf-8').read()
cfg_items=[
 (534,"I;H","P1","衰老过程中屏障通透性的变化与影像学测量"),
 (535,"B;I","P1","缺氧与HIF-1信号对脑内皮屏障的调控"),
 (536,"A;H","P0","中枢PET示踪剂的设计准则与脑渗透"),
]
lines=["CFG={"]
for k,wf,pri,theme in cfg_items:
    lines.append(' %d:("%s","%s","%s"),'%(k,wf,pri,theme))
lines.append("}")
src=re.sub(r"CFG=\{.*?\n\}", lambda m: "\n".join(lines), src, flags=re.S)
open('append_b100.py','w',encoding='utf-8').write(src)
