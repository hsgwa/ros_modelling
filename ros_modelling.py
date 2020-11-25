from typing import List, Union, Any, Callable, Dict
import numpy as np

from .histogram import HistogramReaderFactory
from .application import Application
from .node import Node

def read_json(file_path):
      import json
      with open(file_path) as f:
          arch = json.load(f)
      histogram_reader = HistogramReaderFactory.create(arch['latency_type'])

      app = Application()
      for node_json in arch['nodes']:
          app.add_node(Node.create(histogram_reader, node_json))
      for communication_json in arch['communication']:
          app.set_latency(histogram_reader, communication_json)

      return app
