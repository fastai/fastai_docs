#AUTOGENERATED! DO NOT EDIT! File to edit: dev/01a_dataloader.ipynb (unless otherwise specified).

__all__ = ['Dataset', 'IndexedDataset', 'BaseDS', 'BatchDS', 'dataloader']

from ..imports import *
from ..test import *
from ..core import *
from ..notebook.showdoc import show_doc

from torch.utils.data.dataloader import _MultiProcessingDataLoaderIter,_SingleProcessDataLoaderIter,_DatasetKind
_loaders = (_MultiProcessingDataLoaderIter,_SingleProcessDataLoaderIter)

def _wif(worker_id):
    info = get_worker_info()
    ds = info.dataset
    ds.nw,ds.offs = info.num_workers,info.id
    ds.wif()

class Dataset():
    def __init__(self, items, collate_fn=None):
        if items: items.wrapper = self
        self.items,self.sampler = items,InfiniteSampler()
        if collate_fn: self.collate_fn = collate_fn

    def __iter__(self):
        self.reset()
        return map(self.collate_fn, self.items)

    def collate_fn(self, b): return default_collate(b)
    def __getattr__(self,k): return delegate_attr(k,self,'items')
    def reset(self): pass
    def wif(self): pass

class IndexedDataset(Dataset):
    def __init__(self, items ,bs=1, shuffle=False, sampler=None, batch_sampler=None, drop_last=False,
                 sampler_cls=None, batch_sampler_cls=BatchSampler, collate_fn=default_collate):
        super().__init__(items,collate_fn)
        self.sampler = batch_sampler
        self.rng,self.nw,self.offs,self.is_iterable = random.Random(),1,0,True
        self._delegate_items("get_batches","get_batch","collate")
        if self.sampler: return
        if not sampler: sampler = ifnone(sampler_cls, (SequentialSampler,RandomSampler)[shuffle])(items)
        self.sampler = batch_sampler_cls(sampler, bs, drop_last)

    def __iter__(self):
        torch.manual_seed(self.rng.randint(0,sys.maxsize))
        samps = list(enumerate(self.sampler))
        idxs = (b for i,b in samps if i%self.nw==self.offs)
        return self.get_batches(idxs)

    def get_batch(self, b): return [self.items[j] for j in b]
    def get_batches(self, idxs): return map(self.get_batch, idxs)
    def wif(self) : self.sampler.sampler = copy(self.sampler.sampler)
    def __len__(self): return len(self.sampler)

class BaseDS(GetAttr):
    _xtra = ['show', 'decode', 'show_at', 'decode_at', 'decode_batch']
    def __init__(self, ds):
        self.default = self.ds = ds
        ds.wrapper = self
        self._delegate_ds("reset")

    def _delegate_ds(self, attr):
        if hasattr(self.ds,attr): setattr(self, attr, getattr(self.ds, attr))

    def reset(self): pass

class BatchDS(BaseDS, IterableDataset):
    _xtra = ['show', 'decode', 'show_at', 'decode_at', 'decode_batch']
    def __init__(self, ds ,bs=1, shuffle=False, sampler=None, batch_sampler=None, drop_last=False,
                 collate_fn=default_collate, sampler_cls=None, batch_sampler_cls=BatchSampler):
        self.default,self.ds,self.samp,self.collate_fn = ds,ds,batch_sampler,collate_fn
        self.rng,self.nw,self.offs,self.is_iterable = random.Random(),1,0,True
        for o in ("get_batches","get_batch","collate"): self._delegate_ds(o)
        if self.samp: return
        if not sampler: sampler = ifnone(sampler_cls, (SequentialSampler,RandomSampler)[shuffle])(ds)
        self.samp = batch_sampler_cls(sampler, bs, drop_last)

    def __iter__(self):
        torch.manual_seed(self.rng.randint(0,sys.maxsize))
        samps = list(enumerate(self.samp))
        idxs = (b for i,b in samps if i%self.nw==self.offs)
        return self.get_batches(idxs)

    def get_batch(self, b): return [self.ds[j] for j in b]
    def get_batches(self, idxs): return map(self.get_batch, idxs)
    def collate(self, idxs): return self.collate_fn(self.get_batches(idxs))
    def __len__(self): return len(self.samp)

def _wif(worker_id):
    info = get_worker_info()
    ds = info.dataset
    ds.nw,ds.offs = info.num_workers,info.id
    ds.samp.sampler = copy(ds.samp.sampler)

def dataloader(ds, bs=1, num_workers=0, collate_fn=default_collate, **kwargs):
    if not isinstance(ds, IterableDataset): ds = BatchDS(ds, bs, **kwargs)
    return DataLoader(ds, num_workers=num_workers, batch_size=None,
                      worker_init_fn=_wif, collate_fn=noop)