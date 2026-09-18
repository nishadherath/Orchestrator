export class JobRunner {
  constructor({concurrency = 2, createLimit}) {
    this.limit = createLimit({concurrency, rejectOnClear: true});
    this.promises = [];
  }

  submit(id, work) {
    const promise = this.limit(async () => ({id, value: await work()}));
    this.promises.push(promise);
    return promise;
  }

  async shutdown() {
    this.limit.clearQueue();
    return Promise.allSettled(this.promises);
  }
}
