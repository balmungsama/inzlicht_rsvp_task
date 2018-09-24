function s0_makeDirectories(subjectIDs,rawDataDirectory,outputDirectory)
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

% Written in MATLAB R2017a
% Last modified by John Eusebio 02-08-2018 22:19 hauselin@gmail.com

% subject numbers to match and create directories for
% make sure that they're in the proper format
if class(subjectIDs) == 'char'
    subjectIDs = {subjectIDs};
end

% subdirectories to be created within each participant's folder
newDirectoriesToMake = {'continuous','erp','raw','parameters'}; %'epoched', 'timefreq'

% file extensions to find and copy over
targetFileExtensions = {'.cnt', '.evt', '.sen', '.trg'};

% ensure that there are input & output directories, even if unspecified 
if nargin == 2
    rawDataDirectory = pwd;
elseif nargin == 1
    rawDataDirectory = pwd;
    outputDirectory  = pwd;
end

% make 'EEGData' directory in current directory if it doesn't exist
outputEEGdata = fullfile(outputDirectory, 'EEGData'); % where to move raw data to 

if ~exist(outputEEGdata, 'dir')
    mkdir(outputEEGdata);
end

%% loop through each subject, create directories, subdirectories, and move files into subdirectories
for subj = 1:length(subjectIDs)
    subj = subjectIDs{subj};

    inputSubjDir   = fullfile(rawDataDirectory, subj);
    inputSubjFiles = dir(inputSubjDir);
    inputSubjFiles = {inputSubjFiles.name};

    % find which of the files contain the file extensions of interest
    filesToMove = contains(inputSubjFiles, targetFileExtensions);
    filesToMove = inputSubjFiles(filesToMove);

    if numel(filesToMove) == 0
        disp(['Subject ' subj '`s directory did not contain any files matching target extensions.']);
        disp(strjoin({'Target extensions: ' targetFileExtensions{:}}, ' '));

        continue
    end    

    % Turn the file names into complete file paths
    filesToMove = fullfile( inputSubjDir, filesToMove );

    % create subject-specific EEG output directory
    outputEEGdata_subj = fullfile(outputEEGdata, subj);
    if ~exist(outputEEGdata_subj, 'dir')
        mkdir(outputEEGdata_subj)
    end

    % make subdirectories for each subject
    for subDir = 1:length(newDirectoriesToMake)
        subDir = newDirectoriesToMake{subDir};
        subDir = fullfile(outputEEGdata_subj, subDir);

        if ~exist(subDir, 'dir')
            mkdir(subDir)
        end
    end

    %copy the files to the destination directory
    for file = 1:length(filesToMove)
        file = filesToMove{file};
        
        fileDestination = fullfile(outputEEGdata_subj, 'raw');
        
        copyfile(file, fileDestination);
    end
end

mkdir(fullfile(outputDirectory, 'Binlister'));
mkdir(fullfile(outputDirectory, 'Figures'));
mkdir(fullfile(outputDirectory, 'Figures', 'Subjects'));

end