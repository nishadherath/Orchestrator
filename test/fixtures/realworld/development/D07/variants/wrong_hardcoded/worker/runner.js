export class JobRunner {
  constructor({createLimit}) {
    this.limit = createLimit({concurrency: 1, rejectOnClear: true});
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
