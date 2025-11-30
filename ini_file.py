import os
import configparser
from dataclasses import dataclass
from logging import getLogger, Logger, NullHandler, basicConfig, DEBUG
from typing import Any


@dataclass(frozen=True)
class DefaultParams:
    param_name: str
    config_section: str
    config_key: str
    default_val: Any
    param_type: str


class IniFile:
    def __init__(self,
                 filename: str,
                 logger: Logger = None):
        self.filename = filename
        self._default_params_list: list[DefaultParams] = []

        if logger is not None:
            self._logger = logger
        else:
            self._logger = getLogger(__name__)
            self._logger.addHandler(NullHandler())

        if filename is None:
            _msg = f'ini-file is None'
            self._logger.error(_msg)
            raise ValueError(_msg)

    def load_inifile(self) -> None:
        self._logger.info(f'load inifile')

        if not os.path.isfile(self.filename):
            _msg = f'No ini-file: {self.filename}'
            self._logger.error(_msg)
            raise FileNotFoundError(_msg)

        _config = configparser.ConfigParser()
        _config.optionxform = str
        _config.read(self.filename)

        for _params in self._default_params_list:
            try:
                _val = _config.get(_params.config_section, _params.config_key)

                if _params.param_type == 'float':
                    _val = float(_val)
                elif _params.param_type == 'int':
                    _val = int(float(_val))
                elif _params.param_type == 'str':
                    pass
                else:
                    _msg = f'load_inifile: illegal type: {_params.param_name}'
                    self._logger.error(_msg)
                    raise ValueError(_msg)

            except Exception as err:
                self._logger.error(f'load_inifile: {_params.param_name}')
                self._logger.error(f'load_inifile: {err}')
                raise ValueError(err)

            setattr(self, _params.param_name, _val)

    def set_default_params(self) -> None:
        self._logger.info(f'set default-params')

        for _params in self._default_params_list:
            if _params.param_type not in ['float', 'str', 'int']:
                _msg = f'illegal type: {_params.param_name}'
                self._logger.error(_msg)
                raise ValueError(_msg)

            setattr(self, _params.param_name, _params.default_val)

    def show_params(self) -> None:
        for _params in self._default_params_list:
            _val = getattr(self, _params.param_name, None)

            _msg = f'{_params.param_name} = {_val}'
            self._logger.info(_msg)

    def remake_inifile(self,
                       inifile: str,
                       default_flg: bool = True) -> None:
        self._logger.info(f'remake inifile: {inifile}')

        _config = configparser.ConfigParser()
        _config.optionxform = str

        for _params in self._default_params_list:
            if not _config.has_section(_params.config_section):
                _config.add_section(_params.config_section)

            if default_flg:
                _val = _params.default_val
            else:
                _val = getattr(self, _params.param_name, _params.default_val)

            _config.set(_params.config_section, _params.config_key, str(_val))

        with open(inifile, 'w') as fw:
            _config.write(fw)

    def append_param(self,
                     param_name: str,
                     config_section: str,
                     config_key: str,
                     default: str | float,
                     param_type: str):

        _param = DefaultParams(param_name=param_name,
                               config_section=config_section,
                               config_key=config_key,
                               default_val=default,
                               param_type=param_type)

        if any(p.param_name == param_name for p in self._default_params_list):
            msg = f"append_param: duplicated param_name: {param_name}"
            self._logger.error(msg)
            raise ValueError(msg)

        self._default_params_list.append(_param)


class ViewerIniFile(IniFile):
    def __init__(self,
                 filename: str = 'config.ini',
                 logger: Logger = None):
        super().__init__(filename=filename, logger=logger)

        # Define parameters as None (Recommend for IntelliSense)
        # Variable params
        self.win_size = None
        self.img_num_col = None
        self.img_num_row = None
        self.topmost = None

        # Static params (defined by config-file only)
        self.pix2um = None
        self.img_key = None

        # Define parameters
        self.append_param(param_name='win_size',
                          config_section='GUI', config_key='win_size',
                          default='1000x700', param_type='str')
        self.append_param(param_name='img_num_col',
                          config_section='GUI', config_key='col_num',
                          default=1, param_type='int')
        self.append_param(param_name='img_num_row',
                          config_section='GUI', config_key='row_num',
                          default=1, param_type='int')
        self.append_param(param_name='pix2um',
                          config_section='GUI', config_key='um/pixel',
                          default=1.0, param_type='float')
        self.append_param(param_name='topmost',
                          config_section='GUI', config_key='topmost',
                          default='yes', param_type='str')
        self.append_param(param_name='img_key',
                          config_section='GUI', config_key='img_file_key',
                          default='*.*', param_type='str')


if __name__ == '__main__':
    basicConfig(level=DEBUG)
    logger = getLogger(__name__)

    app = ViewerIniFile(logger=logger)
    # app.set_default_params()
    app.load_inifile()
    app.show_params()
    # app.remake_inifile('config.ini', default_flg=True)
