#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple,List

class ProcessingElement:
    def __init__(self, *process: 'Tuple[Partial[pl.task.Stage[T]], ...]'):
        self._process = list(process)
        print(self._process)

    def add_to_queue(self, queue: 'List[Partial[pl.task.Stage[T]]]'):
        queue += self._process

class PreProcessingElement(ProcessingElement):
    def __init__(self, *process: 'Tuple[Partial[pl.task.Stage[T]], ...]'):
        super().__init__(*process)

class PostProcessingElement(ProcessingElement):
    def __init__(self, *process: 'Tuple[Partial[pl.task.Stage[T]], ...]'):
        super().__init__(*process)