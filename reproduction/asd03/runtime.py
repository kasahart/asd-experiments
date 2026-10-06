# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
# Adapters extend ASDKit (Copyright (c) 2025 Takuya Fujimura; licenses/research-MIT.txt).
"""Install pinned external ASDKit and connect frequency features/checkpoints."""
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def upstream_lock():
    return json.loads((HERE / 'upstream.lock.json').read_text())


def install():
    """Fetch outside the repo, then pip-install without Git or source edits."""
    if sys.prefix == sys.base_prefix:
        raise ValueError('Create a virtual environment before installing ASD03')
    lock = upstream_lock()
    parent = Path(sys.prefix) / 'share/asd03'
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / lock['commit']
    if not root.exists():
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            temporary = Path(temporary)
            archive = temporary / 'upstream.zip'
            with urllib.request.urlopen(lock['url'], timeout=120) as response, archive.open('wb') as stream:
                shutil.copyfileobj(response, stream)
            if digest(archive) != lock['sha256']:
                raise ValueError('Pinned ASDKit archive SHA-256 differs')
            extracted = temporary / 'source'
            with zipfile.ZipFile(archive) as source:
                for member in source.infolist():
                    if not (extracted / member.filename).resolve().is_relative_to(extracted.resolve()):
                        raise ValueError('Archive path escapes extraction directory')
                    if (member.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ValueError('Archive symlinks are not supported')
                source.extractall(extracted)
            children = list(extracted.iterdir())
            if len(children) != 1 or not children[0].is_dir():
                raise ValueError('Expected one archive source directory')
            children[0].rename(root)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--no-build-isolation', '-e', str(root)], check=True)


# Installation needs only the standard library, before ML dependencies exist.
if __name__ == '__main__' and sys.argv[1:] == ['install']:
    install()
    raise SystemExit(0)

sys.path.insert(0, str(HERE.parents[1] / 'src'))
import torch
import torchaudio
from collections.abc import Mapping
from omegaconf import OmegaConf
from pydantic import field_validator
from asdkit.datasets import DCASEWaveCollator as UpstreamWaveCollator
from asdkit.frontends.discriminative_model import BasicDisPLModel
from asdkit.frontends.pretrained_feature.beats import BEATsFrozenModel
from asdkit.models.pretrained_models.beats import BEATsLoRA as UpstreamBEATsLoRA
from asdkit.utils.config_class import MainTrainConfig
from asdkit.utils.dcase_utils import get_dcase_info
from asdkit.utils.dcase_utils.parse_sec import parse_sec_cfg
from asd_min.runner import Encoder
from asd_min.pooling import frequency_pooling, sequence_to_time_frequency

RECORDING_SECONDS = {name: 12 if name in {'ToyCar', 'ToyCarEmu'} else 10 for name in (
    'bearingEmu', 'fan', 'gearboxEmu', 'sliderEmu', 'ToyCar', 'ToyCarEmu', 'valveEmu',
    'BlowerDustCollector', 'Sander', 'SewingMachine', 'ToothBrush', 'ToyDrone')}


def load(path, frame_offset=0, num_frames=-1, normalize=True, channels_first=True, **kwargs):
    import soundfile as sf
    if not normalize:
        raise ValueError('Comparison requires normalized float32 decoding')
    with sf.SoundFile(path) as stream:
        stream.seek(frame_offset)
        data = stream.read(num_frames, dtype='float32', always_2d=True)
        rate = stream.samplerate
    return torch.from_numpy(data.T.copy() if channels_first else data), rate


def restore_beats(ckpt_path, update_cfg=None):
    model = Encoder(ckpt_path, device='cpu', update_cfg=update_cfg).model
    # Encoder is frozen for inference; LoRA construction expects a trainable
    # backbone and applies its own parameter mask. Frozen frontends freeze again.
    return model.train().requires_grad_(True), model.cfg.encoder_embed_dim


class BEATsLoRA(UpstreamBEATsLoRA):
    """Keep upstream ASP/LoRA; use the shared grid-preserving backbone."""
    def construct_model(self, ckpt_path, sr=16000, update_cfg=None, specaug=False):
        if sr != 16000:
            raise ValueError('BEATs frontend expects 16 kHz audio')
        self.specaug = specaug
        return restore_beats(ckpt_path, update_cfg)


class BEATsFrequencyPoolingFrozenModel(BEATsFrozenModel):
    def __init__(self, model_cfg=None, pooling='rdp', gamma=4, eps=1e-8):
        if pooling not in {'mean', 'rdp'}:
            raise ValueError('Expected mean or rdp pooling')
        self.pooling, self.gamma, self.eps = pooling, gamma, eps
        super().__init__(model_cfg=model_cfg)

    def construct_model(self, ckpt_path, update_cfg=None):
        return restore_beats(ckpt_path, update_cfg)[0]

    def extract(self, batch):
        wave = batch['wave']
        if self.device != wave.device:
            self.device = wave.device
            self.model.to(self.device)
        sequence, padding, shape = self.model.extract_features_with_grid(wave, padding_mask=batch.get('padding_mask'))
        features = sequence_to_time_frequency(sequence, shape)
        valid = None if padding is None else ~padding.reshape(sequence.shape[0], *shape)
        pooled = frequency_pooling(features, mode=self.pooling, gamma=self.gamma, eps=self.eps, valid_time_mask=valid)
        return {'embed_freq': pooled, 'embed': pooled.flatten(start_dim=1)}


def plain_values(value):
    if OmegaConf.is_config(value):
        value = OmegaConf.to_container(value, resolve=True)
    if isinstance(value, Mapping):
        return {key: plain_values(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain_values(item) for item in value]
    return str(value) if isinstance(value, Path) else value


class FrequencyDisPLModel(BasicDisPLModel):
    """Keep the classification objective; infer before its ASP projection."""
    def __init__(self, model_cfg, *args, rdp_gamma=4, **kwargs):
        model_cfg = plain_values(model_cfg)
        extractor = model_cfg['extractor_cfg']
        if extractor['tgt_class'] == 'asdkit.models.pretrained_models.beats.BEATsLoRA':
            extractor['tgt_class'] = 'runtime.BEATsLoRA'
        super().__init__(model_cfg=model_cfg, *args, **kwargs)
        self.rdp_gamma = rdp_gamma
        self.save_hyperparameters('rdp_gamma')

    def on_save_checkpoint(self, checkpoint):
        super().on_save_checkpoint(checkpoint)
        checkpoint['hyper_parameters'] = plain_values(self.hparams)
        trainer = self.trainer
        completed = trainer.fit_loop.epoch_progress.total.completed
        checkpoint['training_limits'] = {'max_epochs': trainer.max_epochs, 'max_steps': trainer.max_steps}
        checkpoint['training_complete'] = (
            (trainer.max_steps > 0 and trainer.global_step >= trainer.max_steps)
            or (trainer.max_epochs is not None and completed >= trainer.max_epochs))

    def forward(self, batch):
        backbone = self.extractor.model.get_base_model()
        sequence, padding, shape = backbone.extract_features_with_grid(batch['wave'], padding_mask=batch.get('padding_mask'))
        features = sequence_to_time_frequency(sequence, shape)
        valid = None if padding is None else ~padding.reshape(sequence.shape[0], *shape)
        pooled = frequency_pooling(features, mode='rdp', gamma=self.rdp_gamma, eps=1e-8, valid_time_mask=valid)
        return {'embed_freq': pooled, 'embed': pooled.flatten(start_dim=1)}


class DCASEWaveCollator(UpstreamWaveCollator):
    """Anonymous Evaluation names carry unknown domain/normality (-1)."""
    def format_batch(self, batch):
        paths = [item['path'] for item in batch]
        anonymous = [len(Path(path).name.split('_')) < 5 for path in paths]
        if not any(anonymous):
            return super().format_batch(batch)
        result = {'path': paths}
        result.update({key: [get_dcase_info(path, key) for path in paths]
                       for key in ('machine', 'section', 'attr')})
        for key in ('is_normal', 'is_target'):
            result[key] = [-1 if unknown else get_dcase_info(path, key)
                           for path, unknown in zip(paths, anonymous)]
        result['wave'] = torch.stack([self.crop_wave(item['wave']) for item in batch])
        return result


class ASDTrainConfig(MainTrainConfig):
    @field_validator('dcase', mode='before')
    def check_dcase(cls, value):
        if value != 'dcase2026':
            raise ValueError('ASD03 requires dcase2026')
        return value


def validate_trainable_state(model, state_dict):
    required = {name for name, parameter in model.named_parameters() if parameter.requires_grad}
    missing = required - state_dict.keys()
    if missing:
        raise ValueError(f'Missing trained parameters in resume checkpoint: {sorted(missing)}')


def main():
    module = sys.argv.pop(1)
    if module != 'asdkit.bin.train':
        raise ValueError('Expected asdkit.bin.train (or install)')
    torch.set_num_threads(1)
    # Training uses the pinned Torch defaults; run.py disables cuDNN TF32
    # separately for teacher/inference so each process has an explicit policy.
    torch.set_float32_matmul_precision('highest')
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = True
    torchaudio.load = load
    import lightning.pytorch as pl
    from lightning.pytorch.callbacks import ModelCheckpoint
    original_fit = pl.Trainer.fit
    def fit_with_final_checkpoint(trainer, *args, **kwargs):
        result = original_fit(trainer, *args, **kwargs)
        for callback in trainer.callbacks:
            if isinstance(callback, ModelCheckpoint) and callback.last_model_path:
                trainer.save_checkpoint(callback.last_model_path)
        return result
    pl.Trainer.fit = fit_with_final_checkpoint
    # Config resolves runtime.* under its canonical name, not __main__.
    from runtime import FrequencyDisPLModel as Frontend
    if any('resume_ckpt_path=' in arg for arg in sys.argv):
        Frontend.strict_loading = False
        original_load = Frontend.load_state_dict
        def checked_load(model, state_dict, *args, **kwargs):
            validate_trainable_state(model, state_dict)
            result = original_load(model, state_dict, *args, **kwargs)
            if result.unexpected_keys:
                raise ValueError(f'Unexpected resume checkpoint keys: {result.unexpected_keys}')
            return result
        Frontend.load_state_dict = checked_load
    from asdkit.bin import train
    train.hydra_to_pydantic = lambda cfg: ASDTrainConfig(**parse_sec_cfg(OmegaConf.to_object(cfg)))
    import hydra
    hydra.main(version_base=None, config_path=str(HERE / 'config/train'), config_name='main')(train.main.__wrapped__)()


if __name__ == '__main__':
    main()
