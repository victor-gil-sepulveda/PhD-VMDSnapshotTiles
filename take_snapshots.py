from optparse import OptionParser, OptionValueError
import tempfile
import os
import subprocess
import optparse
import shutil
import math


def wh_size(option, opt_str, value, parser, *args, **kwargs):
    try:
        setattr(parser.values, option.dest, map(int, value.split(',')))
    except:
        raise OptionValueError("You must use a 2-tuple to define width and height (in tiles).")

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", dest="input")
    parser.add_option("-o", dest="output")
    parser.add_option("-f", dest="num_frames", type="int")
    parser.add_option("-v", dest="vmd_vis")
    parser.add_option('-s', dest="dim", type = "string", action="callback", callback=wh_size)
    (options, args) = parser.parse_args()
    
    # Check number of frames
    num_models = int(subprocess.check_output(["egrep", "-c", "^MODEL", options.input])) 
    
    # Calculate the step
    the_step = int(math.floor(float(num_models)/options.num_frames))

    # Generate the new vis file
    if options.vmd_vis is not None:
        vmd_vis = open(options.vmd_vis,"r").read()
    else: 
        vmd_vis = ""
        
    new_vis_lines = """# Fit molecules (from vmd tuts.)
set reference_sel  [atomselect top "protein" frame 0]
set comparison_sel [atomselect top "protein" frame %d]
set transformation_mat [measure fit $comparison_sel $reference_sel]
set move_sel [atomselect top "all" frame %d]
$move_sel move $transformation_mat

# render it
animate goto %d
render TachyonInternal %s
exit
"""
    new_vis = vmd_vis + new_vis_lines

    # Execute the vis file and render
    dir_path  = tempfile.mkdtemp()
    images = []
    for i in range(0, num_models, the_step):
        vis_file_path = os.path.join(dir_path, "%d.vis"%i)
        vis_file = open(vis_file_path, "w")
        images.append(os.path.join(dir_path, "im_%03d.tga"%i))
        vis_file.write(new_vis%(i, i, i, images[-1]))
        vis_file.close()
        #call vmd
        os.system("vmd -dispdev none -e %s"%vis_file_path)
    print  dir_path
    
    #mount everything
    images_glob = os.path.join(dir_path, "im_???.tga")
    os.system("montage -label '%%f' -mode concatenate -tile %dx%d %s out.tga"%(
                                                                  options.dim[0],
                                                                  options.dim[1],
                                                                  images_glob
                                                                  ))
    os.system("convert out.tga out.png")
    
    shutil.rmtree(dir_path)
        