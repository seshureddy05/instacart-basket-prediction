import argparse
import tensorflow as tf
import numpy as np
from scipy.special import expit

import model_helpers
import batch_helpers
import rnnmodel
import features

def get_featslice(featname):
  start = 0
  for i, feat in enumerate(features.FEATURES):
    if feat.name != featname:
      start += feat.arity
    else:
      end = start + feat.arity
      return (start, end)
  assert False, "Couldn't find feature with name {}".format(featname)

def sort_fds(fds):
  def sortkey(deriv_tuple):
    _, derivs = deriv_tuple
    if len(derivs.shape) == 0:
      return derivs
    return derivs.sum()
  for name, derivs in sorted(fds.items(), key=sortkey):
    print '{}\t{}'.format(name, derivs)

# Make a copy of test user, alter some field, and re-run predictions?
# Would take care of multiple derived feats (e.g. DoW onehot + sincos)
def feat_deriv(order_idx, model, session, batcher, pid):
  # we skip the first order when vectorizing
  seqidx = order_idx - 1
  batch = batcher.batch_for_pid(pid)
  _x, _labels, seqlens, _lm, pindexs, _aids, _dids, uids = batch
  feed = model_helpers.feed_dict_for_batch(batch, model)
  y = model.logits[seqidx]
  x = model.input_data
  grad_op = tf.gradients(y, x)
  # Okay, so we're doing a lot of redundant work here I guess
  grads, logits = sess.run([grad_op, model.logits], feed)
  # unwrap
  grads = grads[0]
  logits = logits[0]
  perfeat = {}
  for feat in features.FEATURES:
    featname = feat.name
    a, b = get_featslice(featname)
    assert b > a, '{} >= {}'.format(a, b)
    perfeat[featname] = np.squeeze(grads[0, :seqidx+1, a:b])
  return perfeat, logits[seqidx]

#def main():
if __name__ == '__main__':
  tf.logging.set_verbosity(tf.logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('tag')
  args = parser.parse_args()
  
  hps = model_helpers.hps_for_tag(args.tag)
  hps.is_training = False
  hps.use_recurrent_dropout = False
  hps.batch_size = 1
  model = rnnmodel.RNNModel(hps)
  batcher = batch_helpers.TestBatcher(hps)
  sess = tf.InteractiveSession()
  # Load pretrained weights
  tf.logging.info('Loading weights')
  model_helpers.load_checkpoint_for_tag(args.tag, sess)

  def explore_derivs(order=1, pid=19348):
    fds, logits = feat_deriv(order, model, sess, batcher, pid)
    return fds, logits

  fds, logit = explore_derivs()
  sort_fds(fds)

