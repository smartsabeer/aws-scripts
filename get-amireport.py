#!/usr/bin/python
import re,sys,commands,csv
import os, datetime


def get_account(env):
  env = env
  f1 = open('./accountid', 'r')
  values = f1.readlines()
  for each in values:
    if env in each:
      value = int(each.split()[-1])
  f1.close()
  return value

def create_file_ami(env):
  env = env
  id = get_account(env)
  output = commands.getoutput("aws  --profile %s ec2 describe-images --filters Name=owner-id,Values=%d --query 'Images[*].{ID:Name}'" % (env,id))
  ## generating filename
  today = datetime.datetime.today()
  date = today.strftime('%Y%m%d')
  file = ''.join(['ami-details-',env,'.',date])
  dir = "/home/ec2-user/sabeerz/audit/reports"
  filename = os.path.join(dir, file)
  ## checking above folder availibility
  if os.path.exists(dir):
    with open(filename,'w') as f2:
       f2.write(output)
    f2.close()
  return filename

def get_ami_list(env):
  env = env
  ami_detail = []
  output = commands.getoutput("aws ec2 describe-instances  --profile %s --query 'Reservations[*].Instances[*].{AInstanceId: InstanceId}'" % env)
  #output = 'i-bd46d440\ni-ce37209d\ni-42e51cb8'
  for each_ins in output.split("\n"):
    ami_names = []
    output = commands.getoutput("aws ec2 describe-tags --profile %s --filters Name=resource-id,Values=%s" %(env,each_ins))
    lines = output.split("\n")
    for each_line in lines:
      match = re.search(r'\bName\b', each_line)
      if match:
        ins_name = each_line.split()[-1]
    ip_address = commands.getoutput("aws ec2 describe-instances --profile %s --instance-ids %s" % (env, each_ins))
    for each_ip in ip_address.split("\n"):
      if each_ip.startswith('PRIVATEIPADDRESSES'):
        check = re.search(r'\bTrue\b', each_ip)
        if check:
          match = re.search(r'(\d+\.\d+\.\d+\.\d+)', each_ip)
          if match:
            ip_addr = match.group()
            ami = ins_name+"-"+ip_addr
          #print ">>ami ", ami
    ami_names.insert(0,ami)
    ami_names.insert(1,each_ins)
    ami_names.insert(2,ip_addr)
    ami_detail.append(ami_names)
  return ami_detail

def generate_report(env):

  result = []
  ami_list_file = create_file_ami(env)
  if os.path.isfile(ami_list_file):
    print "filenm: ", ami_list_file
    fopen = open(ami_list_file, 'r')
    text = fopen.read()
  ##getting ami names.
  ami_names = get_ami_list(env)
  for ami_name,ami_id,ami_ipaddr in ami_names:
    data = []
    #print "ins names: ", ami_name
    my_regex = ami_name+"\-[0-9]+[a-zA-Z]+[0-9]+"
    #print "my_regex:::", my_regex
    ami_name_list = re.findall(my_regex, text)
    names = [ each_name.split('-')[-1] for each_name in ami_name_list ]
    count = len(names)
    [ data.append(x) for x in sorted(names) ]
    data.insert(0,ami_id)
    data.insert(1,ami_name)
    data.insert(2,ami_ipaddr)
    data.insert(3,count)
    #data.insert(2,names)
    result.append(data)
  return result
 
def write_report_csv(env):

  data = generate_report(env)
  rows = len(data)
  day = datetime.datetime.today()
  today = day.strftime('%Y%m%d') 
  report_file = ''.join(['Report-', env, today,'.csv'])
  dir = "/home/ec2-user/sabeerz/audit/reports"
  filename = os.path.join(dir, report_file)
  if os.path.exists(dir):
    with open(filename, 'wb') as fp:
       csv_writer = csv.writer(fp)
       for row in range(rows):
         cols = len(data[row])
         #print [ data[row][col] for col in range(cols) ]
         csv_writer.writerow([data[row][col] for col in range(cols)])
    fp.close()
  return "Report %s has been created, please check." % report_file

def main():
  args = sys.argv[1:]
  if not args:
    print 'Usage: ./get-amireport.py --env {prod|qa|dev}'
    sys.exit(1)

  option = args[0]
  env = args[1]

  if option == '--env':
    #print create_file_ami(env)
    #print generate_report(env)
    print write_report_csv(env)
  else:
    print 'unknown env option: ' + option
    sys.exit(1)


# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
  main()


