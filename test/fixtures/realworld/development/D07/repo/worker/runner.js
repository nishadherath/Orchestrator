export class JobRunner {
  constructor({concurrency = 2, createLimit}) {
    if (typeof createLimit !== 'function') {
      throw new TypeError('createLimit must be a function');
    }

    this.limit = createLimit(concurrency);
    this.closed = false;
    this.promises = [];
  }

  submit(id, work) {
    if (this.closed) {
      return Promise.reject(new Error('runner is shut down'));
    }

    const promise = this.limit(async () => ({id, value: await work()}));
    this.promises.push(promise);
    return promise;
  }

  async shutdown() {
    this.closed = true;
    this.limit.clearQueue();
    return Promise.allSettled(this.promises);
  }
}
