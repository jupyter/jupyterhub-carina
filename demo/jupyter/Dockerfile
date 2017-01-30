# Select a notebook type from https://github.com/jupyter/docker-stacks#a-visual-overview-of-stacks
FROM jupyter/minimal-notebook

# Add workshop materials such as Jupyter notebooks and supporting files
ADD materials/* /home/jovyan/work/

# Install additional dependencies
# RUN apt-get update && apt-get install -y <package>
# RUN pip install <package>

# Workaround for https://github.com/getcarina/feedback/issues/31#issuecomment-185523037
USER root

# Use the JupyterHub-friendly startup script
CMD ["/usr/local/bin/start-singleuser.sh"]
