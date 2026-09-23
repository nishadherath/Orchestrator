import pLimit from 'p-limit';

import {JobRunner} from './runner.js';


export function createJobRunner(concurrency = 2) {
  return new JobRunner({concurrency, createLimit: pLimit});
}
