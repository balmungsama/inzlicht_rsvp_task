function s0_makeDirectories(subjectIDs,rawDataDirectory)
% Creates EEGData directory in current directory. 
% Within EEGData, creates a directory for each subject.
% Each subject's directory contains many subdirectories.
% Moves raw EEG data into the Raw data directory within each
% subject's folder.
%
% USAGE 
% s0_makeDirectories('001','cnt','/Users/Dropbox/Data/MyRawData/') % one subject
% s0_makeDirectories({'0001','0002','0003','0013'},'edf','/Users/DataFromEEG/') % multiple subjects at once
% s0_makeDirectories({'0001','0002','0003','0013'},'edf','Raw') % raw data in subdirectory 'Raw'
%
% INPUTS
% subjectIDs: subject IDs STRING to match in your raw data filenames (can also be a CELL array containing multiple subject IDs)
%             partial matching works too: 'EEGStudy001.edf' and 'EEGStudy020.edf' can be matched using just {'001','020'}
% eegdataExtension: STRING extension of raw eeg file 
% rawDataDirectory: raw data directory STRING

% Written in MATLAB R2016b (also tested in 2017b)
% Last modified by Hause Lin 12-06-18 20:23 hauselin@gmail.com

% subject numbers to match and create directories for
subjects = subjectIDs; % subjects in numeric
% subjects = strsplit(num2str(subjects, '%04d '), ' '); % convert numeric to string in cell to match file names and move files accordingly

% eeg raw data filetype

% subdirectories to be created within each participant's folder
newDirectoriesToMake = {'continuous','epoched','erp','raw','timefreq','parameters'}; 

%% Verifying input/output before running

if class(subjects) == 'char'
   subjects = {subjects};
end

clc;

disp(['Trying to match and move ' num2str(length(subjects)) ' subjects']);
disp(subjects);

disp(['Moving data to this folder: ' fullfile(pwd, 'EEGData')]); % where to move raw data from
input(['If correct, press enter. If wrong, press Ctrl-C to stop...']);

if nargin == 2
    directoryToReadFrom = rawDataDirectory; 
    disp(['Reading raw data from' rawDataDirectory]); 
else
    directoryToReadFrom = ''; 
end

disp('Creating these directories within each subject''s directory:');
disp(newDirectoriesToMake)
input(['If correct, press enter. If wrong, press Ctrl-C to stop...']);

%% Start doing stuff. Do not edit unless you know what you're doing...

if isempty(directoryToReadFrom)
    disp('Error! No directory provided!');
    mkdir('dummydirectory');
    directoryToReadFrom = 'dummydirectory';
end

% make 'EEGData' directory in current directory if it doesn't exist
outputDataDirectory = 'EEGData'; % where to move raw data to (subdirectory within current working directory)
if ~exist(outputDataDirectory, 'dir')
    mkdir(outputDataDirectory);
end

clc

%% loop through each subject, create directories, subdirectories, and move files into subdirectories

for subjI = 1:length(subjects)
    
    disp('------------------------------------');
    currentSubject = subjects{subjI}; % get current subject id
    disp(['Subject ' currentSubject]);
    
    subjDirectory = fullfile(pwd, outputDataDirectory, currentSubject);
    
    % move files into correct directory
    try 
        filesInRawDataDirectory = dir(directoryToReadFrom); % list all files in raw data directory
        filesToMove = find(~cellfun(@isempty, strfind({filesInRawDataDirectory.name}, currentSubject))); % indices of files to read
        
        % if subject data are already in separate folders
        if ~isempty(filesToMove)
            while filesInRawDataDirectory(filesToMove(1)).isdir % while the file is a directory, keep going into the subdirectory until it's no longer a directory but a file
                filesInRawDataDirectory = dir(fullfile(filesInRawDataDirectory(filesToMove).folder, currentSubject));
                filesToMove = find(~cellfun(@isempty, strfind({filesInRawDataDirectory.name}, subjects{subjI}))); % indices of files to read
            end
        end
            
        if isempty(filesToMove) && ~exist(subjDirectory, 'dir') % if no files found and subject directory doesn't exist, don't do anything
            % disp(['No files found for subject ' currentSubject ' in ' directoryToReadFrom]);
            disp('------------------------------------');
            
        elseif isempty(filesToMove) && exist(subjDirectory, 'dir') % if no files found but subject directory exists, create new subdirectories if necessary
            % create subdirectories in subject directory if necessary
            for i = 1:length(newDirectoriesToMake)
                newDirectoryI = fullfile(subjDirectory, newDirectoriesToMake{i});
                if ~exist(newDirectoryI, 'dir')
                    mkdir(newDirectoryI)
                end
            end
            % disp(['No files found for subject ' currentSubject ' in ' directoryToReadFrom]);
            disp('Data directory and subdirectories already exist.');
            disp('------------------------------------');
        else % if subject files exist
            if ~exist(subjDirectory, 'dir') % if the subject diretory doesn't exist, make it
                mkdir(subjDirectory);
            end
            % create subdirectories in subject directory
            for i = 1:length(newDirectoriesToMake)
                newDirectoryI = fullfile(subjDirectory, newDirectoriesToMake{i});
                if ~exist(newDirectoryI, 'dir')
                    mkdir(newDirectoryI)
                end
            end
            disp('Created new directories and subdirectories.');
            
            % move files from raw data directory to new subject directory
            for i = filesToMove
                try 
                    fromFile = fullfile(directoryToReadFrom, filesInRawDataDirectory(i).name);
                    toFile = fullfile(subjDirectory, 'raw', filesInRawDataDirectory(i).name);
                    movefile(fromFile, toFile);
                    disp(['Moved ' filesInRawDataDirectory(i).name ' to ' fullfile(outputDataDirectory, currentSubject, 'raw', filesInRawDataDirectory(i).name)]);
                catch
                    fromFile = fullfile(directoryToReadFrom,currentSubject,filesInRawDataDirectory(i).name);
                    toFile = fullfile(subjDirectory, 'raw', filesInRawDataDirectory(i).name);
                    movefile(fromFile, toFile);
                    disp(['Moved ' filesInRawDataDirectory(i).name ' to ' fullfile(outputDataDirectory, currentSubject, 'raw', filesInRawDataDirectory(i).name)]);
                end
            end
            
            disp('Done');
            disp('------------------------------------');
        end
        
    catch
        disp(['Problem with subject ' currentSubject '!']);
        disp('------------------------------------');
    end
    
    if exist('dummydirectory', 'dir')
        rmdir('dummydirectory', 's');
    end
    
    mkdir('Binlister');
    mkdir('Figures');
    mkdir('Figures/Subjects');
end

end