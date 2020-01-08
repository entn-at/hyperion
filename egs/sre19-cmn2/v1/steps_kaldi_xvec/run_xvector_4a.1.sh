#!/bin/bash
# Copyright      2019   Johns Hopkins University (Author: Jesus Villalba)
#                2017   David Snyder
#                2017   Johns Hopkins University (Author: Daniel Garcia-Romero)
#                2017   Johns Hopkins University (Author: Daniel Povey)
#
# Apache 2.0.

# This script trains F-TDNN with layer-width=600

. ./cmd.sh
set -e

stage=1
train_stage=0
use_gpu=true
remove_egs=false
num_epochs=3
nodes=b0
storage_name=$(date +'%m_%d_%H_%M')

data=data/train
nnet_dir=exp/xvector_nnet_4a.2/
egs_dir=exp/xvector_nnet_4a.2/egs
lr=0.001
final_lr=0.0001
batch_size=128
frames_per_iter=100000000
num_repeats=16

. ./path.sh
. ./cmd.sh
. ./utils/parse_options.sh

# Now we create the nnet examples using steps_kaldi_xvec/get_egs.sh.
# The argument --num-repeats is related to the number of times a speaker
# repeats per archive.  If it seems like you're getting too many archives
# (e.g., more than 200) try increasing the --frames-per-iter option.  The
# arguments --min-frames-per-chunk and --max-frames-per-chunk specify the
# minimum and maximum length (in terms of number of frames) of the features
# in the examples.
#
# To make sense of the egs script, it may be necessary to put an "exit 1"
# command immediately after stage 3.  Then, inspect
# exp/<your-dir>/egs/temp/ranges.* . The ranges files specify the examples that
# will be created, and which archives they will be stored in.  Each line of
# ranges.* has the following form:
#    <utt-id> <local-ark-indx> <global-ark-indx> <start-frame> <end-frame> <spk-id>
# For example:
#    100304-f-sre2006-kacg-A 1 2 4079 881 23

# If you're satisfied with the number of archives (e.g., 50-150 archives is
# reasonable) and with the number of examples per speaker (e.g., 1000-5000
# is reasonable) then you can let the script continue to the later stages.
# Otherwise, try increasing or decreasing the --num-repeats option.  You might
# need to fiddle with --frames-per-iter.  Increasing this value decreases the
# the number of archives and increases the number of examples per archive.
# Decreasing this value increases the number of archives, while decreasing the
# number of examples per archive.
if [ $stage -le 6 ]; then
  echo "$0: Getting neural network training egs";
  # dump egs.
  if [[ $(hostname -f) == *.clsp.jhu.edu ]] && [ ! -d $egs_dir/storage ]; then
      dir_name=$USER/hyp-data/kaldi-xvector/$storage_name/egs/storage
      if [ "$nodes" == "b0" ];then
	  utils/create_split_dir.pl \
	      /export/b{04,05,06,07,08,09}/$dir_name $egs_dir/storage
      elif [ "$nodes" == "b1" ];then
	  utils/create_split_dir.pl \
	      /export/b{14,15,16,17}/$dir_name $egs_dir/storage
      elif [ "$nodes" == "fs01" ];then
	  utils/create_split_dir.pl \
	      /export/fs01/$dir_name $egs_dir/storage
      elif [ "$nodes" == "c0" ];then
	  utils/create_split_dir.pl \
	      /export/c{06,07,08,09}/$dir_name $egs_dir/storage
      elif [ "$nodes" == "bc" ];then
	  utils/create_split_dir.pl \
	      /export/{b07,b08,b10,b15,b16,b17,b19,c04,c05,c08,c09,c10}/$dir_name $egs_dir/storage
      fi
  fi
  steps_kaldi_xvec/get_egs.sh --cmd "$train_cmd" \
    --nj 8 \
    --stage 0 \
    --frames-per-iter $frames_per_iter \
    --frames-per-iter-diagnostic 100000 \
    --min-frames-per-chunk 200 \
    --max-frames-per-chunk 400 \
    --num-diagnostic-archives 3 \
    --num-repeats $num_repeats \
    "$data" $egs_dir
fi

if [ $stage -le 7 ]; then
  echo "$0: creating neural net configs using the xconfig parser";
  num_targets=$(wc -w $egs_dir/pdf2num | awk '{print $1}')
  feat_dim=$(cat $egs_dir/info/feat_dim)

  # This chunk-size corresponds to the maximum number of frames the
  # stats layer is able to pool over.  In this script, it corresponds
  # to 100 seconds.  If the input recording is greater than 100 seconds,
  # we will compute multiple xvectors from the same recording and average
  # to produce the final xvector.
  max_chunk_size=10000
  opts="l2-regularize=0.0001"
  linear_opts="orthonormal-constraint=1.0"
  
  # The smallest number of frames we're comfortable computing an xvector from.
  # Note that the hard minimum is given by the left and right context of the
  # frame-level layers.
  min_chunk_size=50
  mkdir -p $nnet_dir/configs
  cat <<EOF > $nnet_dir/configs/network.xconfig
  # please note that it is important to have input layer with the name=input

  # The frame-level layers
  input dim=${feat_dim} name=input
  relu-batchnorm-layer name=tdnn1 input=Append(-2,-1,0,1,2) dim=512 
  linear-component name=tdnn2l dim=180 $linear_opts input=Append(-2,0)
  relu-batchnorm-layer name=tdnn2 $opts input=Append(0,2) dim=725
  linear-component name=tdnn3l dim=180 $linear_opts
  relu-batchnorm-layer name=tdnn3 $opts dim=725
  linear-component name=tdnn4l dim=180 $linear_opts input=Append(-3,0)
  relu-batchnorm-layer name=tdnn4 $opts input=Append(0,3) dim=725
  linear-component name=tdnn5l dim=180 $linear_opts
  relu-batchnorm-layer name=tdnn5 $opts dim=725 input=Append(0, tdnn3l)
  linear-component name=tdnn6l dim=180 $linear_opts input=Append(-3,0)
  relu-batchnorm-layer name=tdnn6 $opts input=Append(0,3) dim=725
  linear-component name=tdnn7l dim=180 $linear_opts input=Append(-3,0)
  relu-batchnorm-layer name=tdnn7 $opts input=Append(0,3,tdnn6l,tdnn4l,tdnn2l) dim=725
  linear-component name=tdnn8l dim=180 $linear_opts input=Append(-3,0)
  relu-batchnorm-layer name=tdnn8 $opts input=Append(0,3) dim=725
  linear-component name=tdnn9l dim=180 $linear_opts 
  relu-batchnorm-layer name=tdnn9 $opts input=Append(0,tdnn7l,tdnn5l,tdnn3l) dim=725
  linear-component name=tdnn10l dim=180 $linear_opts input=Append(-3,0)
  relu-batchnorm-layer name=tdnn10 $opts input=Append(0,3) dim=725
  linear-component name=tdnn11l dim=180 $linear_opts 
  relu-batchnorm-layer name=tdnn11 $opts input=Append(0,tdnn10l,tdnn8l,tdnn6l) dim=725
  linear-component name=tdnn12l dim=180 $linear_opts input=Append(-3,0)
  relu-batchnorm-layer name=tdnn12 $opts input=Append(0,3) dim=725
  linear-component name=tdnn13l dim=180 $linear_opts 
  relu-batchnorm-layer name=tdnn13 $opts input=Append(0,tdnn11l,tdnn9l,tdnn7l) dim=725
  relu-batchnorm-layer name=tdnn14 $opts dim=1800

  # The stats pooling layer. Layers after this are segment-level.
  # In the config below, the first and last argument (0, and ${max_chunk_size})
  # means that we pool over an input segment starting at frame 0
  # and ending at frame ${max_chunk_size} or earlier.  The other arguments (1:1)
  # mean that no subsampling is performed.
  stats-layer name=stats config=mean+stddev(0:1:1:${max_chunk_size})

  # This is where we usually extract the embedding (aka xvector) from.
  relu-batchnorm-layer name=tdnn15 dim=512 input=stats

  # This is where another layer the embedding could be extracted
  # from, but usually the previous one works better.
  relu-batchnorm-layer name=tdnn16 dim=512
  output-layer name=output include-log-softmax=true dim=${num_targets}
EOF

  python2 steps/nnet3/xconfig_to_configs.py \
      --xconfig-file $nnet_dir/configs/network.xconfig \
      --config-dir $nnet_dir/configs/
  cp $nnet_dir/configs/final.config $nnet_dir/nnet.config

  # These three files will be used by sid/nnet3/xvector/extract_xvectors.sh
  echo "output-node name=output input=tdnn15.affine" > $nnet_dir/extract.config
  echo "$max_chunk_size" > $nnet_dir/max_chunk_size
  echo "$min_chunk_size" > $nnet_dir/min_chunk_size
fi

dropout_schedule='0,0@0.20,0.1@0.50,0'
srand=123
if [ $stage -le 8 ]; then
  python2 steps/nnet3/train_raw_dnn.py --stage=$train_stage \
    --cmd="$train_cmd" \
    --trainer.optimization.proportional-shrink 10 \
    --trainer.optimization.momentum=0.5 \
    --trainer.optimization.num-jobs-initial=3 \
    --trainer.optimization.num-jobs-final=8 \
    --trainer.optimization.initial-effective-lrate=$lr \
    --trainer.optimization.final-effective-lrate=$final_lr \
    --trainer.optimization.minibatch-size=$batch_size \
    --trainer.srand=$srand \
    --trainer.max-param-change=2 \
    --trainer.num-epochs=$num_epochs \
    --trainer.dropout-schedule="$dropout_schedule" \
    --trainer.shuffle-buffer-size=1000 \
    --egs.frames-per-eg=1 \
    --egs.dir="$egs_dir" \
    --cleanup.remove-egs $remove_egs \
    --cleanup.preserve-model-interval=10 \
    --use-gpu=true \
    --dir=$nnet_dir  || exit 1;
fi

exit 0;