'''
Created on Nov 10, 2012

@author: Nishant
'''

import re, json, os

def main():
    choice = input('1 = extract MIMs, 2 = strip trailing characters')
    if int(choice) == 1:
#        dis_file_path = input('Path to diseases file: ')
#        new_file_path = input('Path to new file: ')
        dis_file_path = 'C:\Users\Nishant\Documents\SuLab\GoogleAppEngine\MobileAnnotationGame\Diseases.csv'
        new_file_path = 'C:\Users\Nishant\Documents\Intel\DOID2MIM.csv'
        dis_file = open(dis_file_path)
        new_file = open(new_file_path, 'w')
        Xrefs2MIM(dis_file, new_file)
    elif int(choice) == 2:
        old_file_p = input('Old file: ')
        new_file_path= input('Path to new file: ')
        old_file_path = os.path.join(os.path.split(__file__)[0], old_file_p)
#        old_file_path = 'C:\Users\Nishant\Documents\SuLab\GoogleAppEngine\MobileAnnotationGame\Relations.csv'
#        new_file_path = 'C:\Users\Nishant\Documents\Intel\MobiangaData.csv'
        old_file = open(old_file_path)
        new_file = open(new_file_path, 'w')
        strip(old_file, new_file)
    else:
        print('Not one of the choices')

def Xrefs2MIM(diseases_file, new_file):
    old = diseases_file.readlines()
    for l in old:
        ncbim = re.search('(\d+)', l)
        ncbi = ncbim.group()
        mimm = re.search('OMIM:(\d+)', l)
        if mimm is None:
            mim = ' - '
        else:
            mim = mimm.group(1)
        line = '{ncbi},{mim}\n'.format(ncbi = ncbi, mim = mim)
        new_file.write(line)
    
def strip(old_file, new_file):
    old = old_file.readlines()
    for line in old:
        new_file.write(line.rstrip() + '\n')
        
        
if __name__ == '__main__':
    main()