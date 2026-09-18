function abortError() {
  const error = new Error('Job was cleared');
  error.name = 'AbortError';
  return error;
}

export class JobRunner {
  constructor({concurrency = 2, createLimit}) {
    if (typeof createLimit !== 'function') {
      throw new TypeError('createLimit must be a function');
    }

    this.limit = createLimit(concurrency);
    this.closed = false;
    this.records = [];
  }

  submit(id, work) {
    if (this.closed) {
      return Promise.reject(new Error('runner is shut down'));
    }

    const record = {id, state: 'queued'};
    const promise = new Promise((resolve, reject) => {
      record.resolve = resolve;
      record.reject = reject;
    });
    record.promise = promise;
    this.records.push(record);

    const scheduled = this.limit(async () => {
      record.state = 'running';
      try {
        record.resolve({id, value: await work()});
      } catch (error) {
        record.reject(error);
      } finally {
        record.state = 'settled';
      }
    });
    scheduled.catch(() => {});
    return promise;
  }

  async shutdown() {
    this.closed = true;
    for (const record of this.records) {
      if (record.state === 'queued') {
        record.state = 'settled';
        record.reject(abortError());
      }
    }
    this.limit.clearQueue();
    return Promise.allSettled(this.records.map(record => record.promise));
  }
}
