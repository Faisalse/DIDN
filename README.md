<!DOCTYPE html>
<html>
<head>

</head>

<h2>Installation guide</h2>  
<p>This is how the framework can be downloaded and configured to run the experiments</p>
<h5>Using Docker</h5>
<ul>
  <li>Download and install Docker from <a href="https://www.docker.com/">https://www.docker.com/</a></li>
  <li>Run the following command to "pull Docker Image" from Docker Hub: <code>docker pull shefai/intent_aware_recomm_systems</code>
  <li>Clone the GitHub repository by using the link: <code>https://github.com/Faisalse/DIDN.git</code>
  <li>Move into the <b>DIDN</b> directory</li>
  
  <li>Run the command to mount the current directory <i>DIDN</i> to the docker container named as <i>Intent_Aware_container</i>: <code>docker run --name Intent_Aware_container  -it -v "$(pwd):/DIDN" -it shefai/intent_aware_recomm_systems</code>. If you have the support of CUDA-capable GPUs then run the following command to attach GPUs with the container: <code>docker run --name Intent_Aware_container  -it --gpus all -v "$(pwd):/DIDN" -it shefai/intent_aware_recomm_systems</code></li> 
<li>If you are already inside the runing container then run the command to navigate to the mounted directory <i>DIDN</i>: <code>cd /DIDN</code> otherwise starts the "Intent_Aware_container"</li>
<li>Finally, follow the given instructions to run the experiments</li>
</ul>  
<h5>Using Anaconda</h5>
  <ul>
    <li>Download Anaconda from <a href="https://www.anaconda.com/">https://www.anaconda.com/</a> and install it</li>
    <li>Clone the GitHub repository by using this link: <code>https://github.com/Faisalse/DIDN.git</code></li>
    <li>Open the Anaconda command prompt</li>
    <li>Move into the <b>DIDN</b> directory</li>
    <li>Run this command to create virtual environment: <code>conda create --name Intent_Aware_env python=3.8</code></li>
    <li>Run this command to activate the virtual environment: <code>conda activate Intent_Aware_env</code></li>
    <li>Run this command to install the required libraries for CPU: <code>pip install -r requirements_cpu.txt</code>. However, if you have support of CUDA-capable GPUs, 
        then run this command to install the required libraries to run the experiments on GPU: <code>pip install -r requirements_gpu.txt</code></li>
    <li>Finally, follow the given instructions to run the experiments</li>
  </ul>
</p>
<h2>Follow these steps to reproduce the models</h2>

<ul>
<li>Download <a href="https://www.dropbox.com/sh/n281js5mgsvao6s/AADQbYxSFVPCun5DfwtsSxeda?dl=0" target="_blank">Yoochoose</a> dataset, unzip it and put the “yoochoose-clicks.dat” file into the “data” directory/folder. </li>
<li>Run this command to reproduce the experiments for the DIDN and baseline models on the shorter version of the Yoochoose dataset: <code>python run_experiments_for_DIDN_baseline_models.py --dataset yoochoose1_64</code> and run the following command to create the experiments for the larger version of the Yoochoose dataset <code>python run_experiments_for_DIDN_baseline_models.py --dataset yoochoose1_4</code>  </li>
<li>Download <a href="https://www.dropbox.com/sh/n281js5mgsvao6s/AADQbYxSFVPCun5DfwtsSxeda?dl=0" target="_blank">Diginetica</a> dataset, unzip it and put the “train-item-views.csv” file into the “data” directory/folder. </li>
<li>Run this command to reproduce the experiments for the DIDN and baseline models on the Diginetica dataset: <code>python run_experiments_for_DIDN_baseline_models.py --dataset diginetica</code></li> 

</ul>
</body>
</html>  

