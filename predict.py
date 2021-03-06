#!/usr/bin/env python

import time
import csv
import argparse
import numpy as np

from baskets import common, user_wrapper
from baskets import predictor as pred
from baskets.time_me import time_me

def main():
  parser = argparse.ArgumentParser(description="Generate a Kaggle submission file")
  parser.add_argument('tag')
  parser.add_argument('--recordfile', default='ktest.tfrecords', 
      help='tfrecords file with the users to make predictions on (default: ktest.tfrecords)')
  parser.add_argument('--mc-trials', type=int, default=50,
      help='Number of rounds of monte carlo sim to perform per product/threshold (default:50)')
  parser.add_argument('-n', '--n-users', type=int, 
      help='Limit number of users tested on (default: no limit)')
  parser.add_argument('--quick', action='store_true') # TODO: hook me up
  parser.add_argument('--save-tag', default='')
  args = parser.parse_args()
  
  t0 = time.time()

  user_iterator = user_wrapper.iterate_wrapped_users(args.recordfile, ktest=True)
  outname = 'submission_{}.csv'.format(args.save_tag)
  f = open(outname, 'w')
  writer = csv.DictWriter(f, fieldnames=['order_id', 'products'])
  writer.writeheader()
  def predcol(pids):
    stringify = lambda pid: 'None' if pid == -1 else str(pid)
    return ' '.join(map(stringify, pids))
  pmap = common.pdict_for_tag(args.tag, args.recordfile)
  predictor = pred.HybridThresholdPredictor(pmap, ntrials=args.mc_trials)
  for i, user in enumerate(user_iterator):
    predicted = predictor.predict_last_order(user)
    oid = user.user.testorder.orderid
    row = {'order_id': oid, 'products': predcol(predicted)}
    writer.writerow(row)
    if args.n_users and i >= args.n_users:
      break
  t1 = time.time()
  print "Finished predictions in {:.1f}s".format(t1-t0)
  
if __name__ == '__main__':
  with time_me(mode="print"):
    main()
