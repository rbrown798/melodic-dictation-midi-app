import mido
import random
mido.set_backend('mido.backends.pygame')
import time
import configparser
import argparse


NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']


class MainApp:
    def __init__(self, needs_config=False):
        self._notes = []
        self._inport = None
        self._outport = None
        self._needs_config = needs_config

    def run(self):
        if not self._get_midi_availability():
            print('Midi unavailable.')
            return False

        self._setup_midi_io()
        self._running = True
        print('(Press Ctrl+C to exit)')

        try:
            while self._running:
                self._generate_melody()
                print('First note:', NOTE_NAMES[self._notes[0] % 12])

                correct = False
                while not correct:
                    self._play_melody()
                    correct = self._capture_response()
                    time.sleep(0.5)
        
        except KeyboardInterrupt:
            self._exit()

    def _get_midi_availability(self):
        available_inputs = mido.get_input_names()
        available_outputs = mido.get_output_names()

        if not (available_inputs and available_outputs):
            return False

        return True

    def _setup_midi_io(self):
        config = self._get_config()

        if config is None or self._needs_config:
            self._set_midi_config()

        else:
            self._restore_midi_config(config)

    def _get_config(self):
        config = configparser.ConfigParser()
        if config.read('config.ini'):
            return config

        return None

    def _set_midi_config(self):
        input_name = self._get_midi_input_name()
        output_name = self._get_midi_output_name()

        config = configparser.ConfigParser()
        config['MIDI'] = {'input_name': input_name, 'output_name': output_name}
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

        self._inport = mido.open_input(input_name)
        self._outport = mido.open_output(output_name)

    def _restore_midi_config(self, config):
        available_inputs = mido.get_input_names()
        available_outputs = mido.get_output_names()

        input_name = available_inputs[0]
        output_name = available_outputs[0]

        config_input_name = config.get('MIDI', 'input_name')
        config_output_name = config.get('MIDI', 'output_name')

        if config_input_name in available_inputs:
            input_name = config_input_name 

        if config_output_name in available_outputs:
            output_name = config_output_name

        self._inport = mido.open_input(input_name)
        self._outport = mido.open_output(output_name)
        
    def _exit(self):
        self._inport.close()
        self._outport.close()
        print('Done.')
        
    def _generate_melody(self):
        self._notes = [random.randint(60, 72) for i in range(3)]

    def _play_melody(self):
        for note in self._notes:
            msg = mido.Message('note_on', note=note, velocity=100, channel=0)
            self._outport.send(msg)
            time.sleep(0.5)
            msg = mido.Message('note_on', note=note, velocity=0, channel=0)
            self._outport.send(msg)

    def _capture_response(self):
        input_notes = []

        while len(input_notes) < len(self._notes):
            self._reset_inport()
            msg = self._inport.receive()
 
            if msg.type == 'note_on':
                input_notes.append(msg.note)
 
            if input_notes != self._notes[:len(input_notes)]:
                print('incorrect')
                return False
        
        print('correct')
        return True
    
    def _get_selection(self, options):
        for i, name in enumerate(options):
            print(f'[{i}] {name}')
        
        user_input = input()

        while not (user_input and user_input.isdigit() 
                   and int(user_input) in range(len(options))):

            print('Invalid input.')
            user_input = input()

        option_id = int(user_input)
        return options[option_id]

    def _reset_inport(self):
        for msg in self._inport.iter_pending():
            pass

    def _get_midi_output_name(self):
        output_names = mido.get_output_names()
        print('Select output device:')
        return self._get_selection(output_names)
    
    def _get_midi_input_name(self):
        input_names = mido.get_input_names()
        print('Select input device:')
        return self._get_selection(input_names)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--setup-midi', action='store_true', 
        help='Configure MIDI IO when program starts')
    args = parser.parse_args()

    app = MainApp(args.setup_midi)
    app.run()


if __name__ == '__main__':
    main()
