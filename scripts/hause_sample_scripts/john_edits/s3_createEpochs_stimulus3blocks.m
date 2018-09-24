function s3_createEpochs_stimulus3blocks(subject)
%% Epoch data and detect artifact in epochs using EEGLAB artifact detection procedures
% Last modified by Hause Lin 28-07-18 22:45 hauselin@gmail.com
% Stimulus-locked
% 3 blocks: natural, health, taste
% trials with valid responses (exclude trials without responses)

%% Set up parameters and read data

% subject = '015'; % subject id

binlister = 'Stimulus_3blocks.txt';
epochRange = [-2500 2500]; % ms
epochBaselineCorrect = [-200 0]; % ms
plotSave = true; % plot and save figures
epochSave = true; % save epoched data?
tfrSave = true; % save time-frequency data?
% binSeparateSets = false; % save each bin as separate sets
dataDirectory = 'EEGData'; % directory containing subject/participant data

currentDir = pwd; % current directory
parentDir = currentDir(1:end-8); % remove 'Scripts' from path

% TODO: import the current subject's event data
% try reading eventlist csv
% try 
%     readtable(fullfile(parentDir, 'Trial event info', [num2str(str2num(subject)) '_trialEventInfo.csv']),'TreatAsEmpty','NA');
% catch
%     disp(['No trialEventInfo csv for subject ' subject, '!']);
%     dlmwrite(fullfile(parentDir,'Messages',['No trialEventInfo csv for subject ' subject ' ' datestr(datetime('now')) '.txt']),['No trialEventInfo csv for subject ' subject ' ' datestr(datetime('now'))],'delimiter','');
%     return
% end

% TODO: These need to be changed to my own.
% add paths
addpath('/psyhome/u4/linhause/matlabtoolboxes/eeglab14_1_2b'); % addpath on UTSC cluster
addpath('/users/hause/dropbox/Apps/MATLAB Toolboxes and Packages/eeglab14_1_2b') % add path on local machine
addpath('/Users/Hause/Dropbox/Apps/MATLAB Toolboxes and Packages/fieldtrip-20180723/')
ft_defaults

%% start analysing data

try 
    dataDirectoryAbsPath = fullfile(parentDir, dataDirectory); 
    currentSubjectDirectory = fullfile(dataDirectoryAbsPath, subject);
    
    clc;
    if ~exist(fullfile(currentSubjectDirectory),'dir') % if directory folder doesn't exist, skip this subject
        disp(['Subject ' subject, ' directory is unavailable']);
        return
    end
    disp(['Subject ' subject, '']);

    directoryToReadFrom = fullfile(currentSubjectDirectory,'continuous'); % directory with data
    filesInDirectory = dir(directoryToReadFrom); % files in data directory
    fileIdx = find(~cellfun(@isempty, strfind({filesInDirectory.name}, 'ICAPruned_Reref.set'))); % index of file to read

    if length(fileIdx) ~= 1 % if more than one raw data found, error
        error('Check number of files in data directory!');
    end

    % Read data with ICA components removed
    [ALLEEG EEG CURRENTSET ALLCOM] = eeglab; % run eeglab
    EEG = pop_loadset('filename',filesInDirectory(fileIdx).name,'filepath',directoryToReadFrom);
    
    % eeglab redraw
    % check events
    % pop_squeezevents(EEG); % summarize events (ERPLAB)
    % eeg_eventtypes(EEG) % summarize events (EEGLAB)
    close all;
    
    %% Create eventlist, assign bins, and extract epochs using ERPLAB

    % create eventlist with ERPLAB and save it in results folder
    outPath = fullfile(parentDir,'Results','Eventlist_erplab'); mkdir(outPath);
    EEG = pop_creabasiceventlist(EEG,'AlphanumericCleaning','on','BoundaryNumeric',{-99},'BoundaryString',{'boundary'},'Eventlist',fullfile(outPath,[EEG.subject '_eventlist_raw.txt']));
    
    % assign bins with ERPLAB binlister
    EEG = pop_binlister(EEG,'BDF',fullfile(parentDir,'Binlister',binlister),'ExportEL',fullfile(outPath,[EEG.subject '_' binlister]),'IndexEL',1,'SendEL2','EEG','UpdateEEG','on','Voutput','EEG');

    % extract epochs with ERPLAB
    if ~isempty(epochBaselineCorrect)
        EEG = pop_epochbin(EEG,epochRange,epochBaselineCorrect); % extract epochs with baseline correction
    else
        EEG = pop_epochbin(EEG,epochRange,'none'); % no baseline correction
    end

    EEG.bindescr = {EEG.EVENTLIST.bdf.description}; % bin description
    EEG = eeg_checkset(EEG);
    [ALLEEG,EEG,CURRENTSET] = eeg_store(ALLEEG,EEG,CURRENTSET);
    disp('Extracted epochs!');
    
    % Check if time-locking events in epochs match: EEG.EVENTLIST.eventinfo.bini & EEG.EVENTLIST.eventinfo.bepoch
    timelockeventsbepoch = [[EEG.EVENTLIST.eventinfo.bepoch] > 0]; 
    if sum([EEG.EVENTLIST.eventinfo(timelockeventsbepoch).bini] == -1)
        error('Error! Check EEG.EVENTLIST.eventinfo.bini and EEG.EVENTLIST.eventinfo.bepoch!'); % NOTE: this is critical
    else
        disp('Epoched data and events match!')
    end

    %% Artifact detection on epoched data with EEGLAB

    % if already run artifact detection, skip it by reloading previous detection parameters
    if exist(fullfile(currentSubjectDirectory,'parameters',[EEG.subject '_bin_' strrep(binlister,'.txt','') '_EEGRejectField.mat']),'file')

        % load artifact detection and rejected epoch information from .mat file
        disp('Not rerunning artifact detection...');
        disp('Overwriting existing EEG.reject with previously saved EEG.reject stored in .mat file...');
        disp([EEG.subject '_bin_' strrep(binlister,'.txt','') '_EEGRejectField.mat']);
        load(fullfile(currentSubjectDirectory,'parameters',[EEG.subject '_bin_' strrep(binlister,'.txt','') '_EEGRejectField.mat']));
        EEG.reject = EEGRejectField;
        EEG = eeg_checkset(EEG);
        
        % find([EEG.EVENTLIST.eventinfo.flag]);
        EEG = pop_syncroartifacts(EEG,'Direction','eeglab2erplab'); % transfer EEG.reject (eeglab) info to EEG.EVENTLIST (erplab)
        EEG = eeg_checkset(EEG);
        [ALLEEG,EEG,CURRENTSET] = eeg_store(ALLEEG,EEG,CURRENTSET);

    else % run artifact detection

        % Citation: Delorme, A., Sejnowski, T., & Makeig, S. (2007). Enhanced detection of artifacts in EEG data using higher-order statistics and independent component analysis. NeuroImage, 34(4), 1443-1449. doi:10.1016/j.neuroimage.2006.11.004
        disp('Detecting artifacts...');

        % exclude eye and EMG channels from artifact detection
        eyeEmgChans = {'SO1','IO1','SO2','IO2','LO1','LO2','CorsOut','CorsIns','CORRins','CORRout','ZYGup','ZYGlow','COORins','COORout'}; % chan to exclude
        allChannels = {EEG.chanlocs.labels}; % all channel labels
        channelsToDetectArtifact = find(~ismember(allChannels, eyeEmgChans)); % exclude channels above

        % reject by linear trend/variance (max slope, uV/epoch: 100; R-squred limit: 0.5)
        EEG = pop_rejtrend(EEG,1,channelsToDetectArtifact,EEG.pnts,100,0.5,0,0,0);
        disp(['Trials rejected via linear trend/variance: ' num2str(find(EEG.reject.rejconst))]);

        % reject by probability (5 SD)
        EEG = pop_jointprob(EEG,1,channelsToDetectArtifact,5,5,0,0,0,[],0);
        disp(['Trials rejected via probability (5 SD): ' num2str(find(EEG.reject.rejjp))]);

        % reject by spectra (detect muscle and eye movement)
        % muscle: -100 to 100 dB, 20 to 40 Hz
        % eye: -50 to 50 dB, 0 to 2 Hz
        EEG = pop_rejspec(EEG,1,'elecrange',channelsToDetectArtifact,'method','fft','threshold',[-50 50;-100 25],'freqlimits',[0 2;20 40],'eegplotcom','','eegplotplotallrej',0,'eegplotreject',0);
        disp(['Trials rejected via spectra: ' num2str(find(EEG.reject.rejfreq))]);

        % update EEG.reject.rejglobal and EEG.reject.rejglobalE fields with all rejected epochs
        EEG = eeg_rejsuperpose(EEG,1,1,1,1,1,1,1,1); 

        % save EEG.reject field as a .mat file so don't need to rerun artifact detection again in the future
        EEGRejectField = EEG.reject;
        save(fullfile(currentSubjectDirectory,'parameters',[EEG.subject '_bin_' strrep(binlister,'.txt','') '_EEGRejectField.mat']),'EEGRejectField'); % save just EEG.reject (maybe this will 
        disp('Finished artifact detection and saved EEG.reject field to parameters folder');
        
        % find([EEG.EVENTLIST.eventinfo.flag]);
        EEG = pop_syncroartifacts(EEG,'Direction','eeglab2erplab'); % transfer EEG.reject (eeglab) info to EEG.EVENTLIST (erplab)
        EEG = eeg_checkset(EEG);
        [ALLEEG,EEG,CURRENTSET] = eeg_store(ALLEEG,EEG,CURRENTSET);
    end

    % save subject's artifact information into subject's parameters directory
    colNames = {'subject','epochs','rejLinear','rejProb','rejSpec','rejTotal','rejPerc','acceptTotal','acceptPerc','binlister'};
    values = {EEG.subject,EEG.trials,length(find(EEG.reject.rejconst)),length(find(EEG.reject.rejjp)),length(find(EEG.reject.rejfreq)),length(find(EEG.reject.rejglobal)),round(length(find(EEG.reject.rejglobal))/EEG.trials*100,2),EEG.trials-length(find(EEG.reject.rejglobal)),round((EEG.trials-length(find(EEG.reject.rejglobal)))/EEG.trials*100,2),binlister};
    T = cell2table(values,'VariableNames',colNames);
    outPath = fullfile(parentDir,'Results','ArtifactInfo'); mkdir(outPath);
    writetable(T, fullfile(outPath,[EEG.subject '_bin_artifactN_' binlister]),'delimiter',',');
    disp('Saved artifact information to parameters directory');

    % gather all subject's artifact detection summary in a table as save as csv file in Binlister directory
    % tempFiles = dir(fullfile(dataDirectoryAbsPath,'**','parameters','',['*_bin_artifactN_' binlister])); % find matching files recursively (only works for MATLAB 2016b onwards)
    % gather all subject's artifact detection summary in a table as save as csv file in Binlister directory
    artifactTableAllSubjects = table();
    tempFiles = dir(fullfile(outPath,['*_bin_artifactN_' binlister])); % find matching files recursively
    filePaths = {tempFiles.name};
    for i=1:length(filePaths)
        tempData = readtable(fullfile(outPath,filePaths{i}));
        artifactTableAllSubjects = [artifactTableAllSubjects; tempData];
    end
    artifactTableAllSubjects.reject = artifactTableAllSubjects.rejPerc > 25; % if > 25% trials rejected, mark subject to reject
    artifactTableAllSubjects = [table([1:height(artifactTableAllSubjects)]') artifactTableAllSubjects]; % add subject number count
    artifactTableAllSubjects.Properties.VariableNames{1} = 'subjectN';

    writetable(artifactTableAllSubjects,fullfile(outPath,['_artifactSummary_' strrep(binlister,'.txt','') '.csv']));
    disp('Saved all subject''s artifact information to directory');

    %% Save single-trial event information

    el = EEG.EVENTLIST.eventinfo; % save ERPLAB eventlist structure
    timeLockedEventsIdx = [el.bepoch] ~= 0; % find indices with time-locked events (bepoch is not 0)
    allEvents = {el.binlabel}; % all event labels (B1, B2 etc.)
    epochEvent = allEvents(timeLockedEventsIdx); % event/code for every epoch (including epochs with artifacts)
    % find artifact and no-artifact epochs
    artifactFlags = [el.flag];
    cleanEpochs = find(~artifactFlags(timeLockedEventsIdx)); % epoch (indices) without artifacts
    
    if ((length(cleanEpochs) + sum(artifactFlags)) ~= EEG.trials) || (length(epochEvent) ~= EEG.trials) % my manual count of trials and EEG.trials should match
        error('Error! Trial numbers don''t match! Double check!');
    end

    % Save single-trial info (design matrix) as table
    elT = struct2table(el);
    elT.enable = []; elT.dura = []; elT.codelabel = []; % remove variables
    % add subject id to table
    C = cell(size(elT,1),1); % empty cell to store subject id
    C(:) = {EEG.subject}; % fill empty cell with subject id
    elT = [C elT]; % join cell with table
    elT.Properties.VariableNames = {'subject','eventN','eventCode','binlabel','timeS','samplingPoint','artifactFlag','binIndicator','epochN'}; % rename variable names
    
    % add extra trial info
    % trialInfo = readtable(fullfile(parentDir, 'Trial event info', [num2str(str2num(subject)) '_trialEventInfo.csv']),'TreatAsEmpty','NA');
    % trialInfo.subject = C; % make sure subject id matches
    % trialInfo.timeS = []; % remove timeS column (can cause errors joining later)

    % elT = outerjoin(elT,trialInfo,'Type','left','Mergekeys',true); % join
    
    elT.bindescr = elT.binlabel; % assign bindescr to each epoch
    for i=1:size(elT,1) %  for each event...
        bindescrTemp = elT{i,'bindescr'}{1}; % get binlabel
        if strcmpi(bindescrTemp,'""') % if empty, it's not time-locking event
            elT{i,'bindescr'}{1} = '';
        else  % if not empty, fill in bindescr from ERP 
            elT{i,'bindescr'}{1} = EEG.bindescr{elT{i,'binIndicator'}};
        end
    end

    % elT.rt = [NaN; diff(elT.timeS)]; % compute RT (change this line accordingly for different designs/experiments)
    % elT.rt(elT.artifactFlag == 1) = NaN; % convert artifact epochs to NaN
    el_timelockevent = elT((elT.epochN ~= 0),:); % eventlist with just time-locked event info
    % save data
    outPath = fullfile(parentDir,'Results','TrialEventInfo',strrep(binlister,'.txt','')); mkdir(outPath);
    writetable(elT,fullfile(outPath,[EEG.subject '_eventAllEvents.csv'])) % all events
    writetable(el_timelockevent,fullfile(outPath,[EEG.subject '_eventTimeLockedEvents.csv'])) % only time-locked events
    disp('Saved event list as txt and csv files');
    
    %% Create design matrix or array of events
   
    % variable names to save together with matfile later on
    % specify which variables to store in design matrix (only numbers, no text!!)
    epochs_allVars = {'epochN','artifactFlag','binIndicator','food','block','familiar','health','like','taste','choice4','choice2','rt','controlSuccess'};
    epochs_all = el_timelockevent(:,epochs_allVars);
    % ensure all variables are double
    for i = 1:length(epochs_allVars)
       if class(epochs_all.(i)) ~= 'double'
           epochs_all.(i) = double(epochs_all.(i));
       end
    end
    
    % create array
    epochs_all = table2array(epochs_all);
    if sum(epochs_all(:,1) < 0) || sum(epochs_all(:,3) < 0)
        error('Error! Check design matrix epoch number and bin number!');
    end

    epochs_all(:,2) = epochs_all(:,2) == 0; % convert artifacts rejected to artifacts accepted
    epochs_clean = epochs_all(epochs_all(:,2) == 1,:); % select only epochs without artifacts
    epochs_clean = epochs_clean((sum(isnan(epochs_clean),2) == 0),:); % select only epochs without NaN
    
    EEG.epochs_all = epochs_all;
    EEG.epochs_clean = epochs_clean;
    EEG.epochs_allVars = epochs_allVars;

    % epochs_all and epochs_clean
    outPath = fullfile(parentDir,'Results','DesignMatrix',strrep(binlister,'.txt','')); mkdir(outPath);
    dlmwrite(fullfile(outPath,[EEG.subject '_epochsAll_designMat.txt']),epochs_all,'delimiter','\t')
    save(fullfile(outPath,[EEG.subject '_epochsAll_designMat.mat']),'epochs_all','epochs_allVars');
    dlmwrite(fullfile(outPath,[EEG.subject '_epochsClean_designMat.txt']),epochs_clean,'delimiter','\t')
    save(fullfile(outPath,[EEG.subject '_epochsClean_designMat.mat']),'epochs_clean','epochs_allVars');
    disp('Saved design matrix as txt and mat files');

    %% Select only clean epochs
    
    % change SO2 to Corr
    chanIdx = find(ismember({EEG.chanlocs.labels},'Corr'));
    EEG.chanlocs(chanIdx) = EEG.chanlocs(ismember({EEG.chanlocs.labels},'SO2'));
    EEG.chanlocs(chanIdx).labels = 'Corr';
    EEG.chanlocs(chanIdx).urchan = chanIdx;

    % change IO2 to Zygo
    chanIdx = find(ismember({EEG.chanlocs.labels},'Zygo'));
    EEG.chanlocs(chanIdx) = EEG.chanlocs(ismember({EEG.chanlocs.labels},'IO2'));
    EEG.chanlocs(chanIdx).labels = 'Zygo';
    EEG.chanlocs(chanIdx).urchan = chanIdx;

    EEG = eeg_checkset(EEG);
    EEG = pop_select(EEG,'nochannel',{'SO2' 'IO2'}); % remove eye channels
    EEG = eeg_checkset(EEG);
    [ALLEEG EEG CURRENTSET] = eeg_store(ALLEEG,EEG,1);
    
    % create new EEG structure for just relevant epochs
    epochsRelevantIdx = epochs_clean(:,1)';
    EEG = pop_select(ALLEEG(1),'trial',epochsRelevantIdx); % select only clean epochs 
    EEG.setname = [EEG.subject '_clean_epochs'];
    EEG.filename = EEG.setname;
    EEG.history = [];
    EEG = eeg_checkset(EEG);
    [ALLEEG EEG CURRENTSET] = eeg_store(ALLEEG,EEG);
    EEG = eeg_retrieve(ALLEEG,1); CURRENTSET = 1; % retrieve first dataset (with all bins)
    EEG = eeg_checkset(EEG);
    
    if epochSave
        outPath = fullfile(parentDir,'Results','Epoch_stimulus_3blocks'); mkdir(outPath);
        ALLEEG(2).history = [];
        EEG = pop_saveset(ALLEEG(2),'filename',[EEG.subject '_epochsClean.set'],'filepath',outPath);
    end
    
    %% Create and save ERPset using ERPLAB

    ERP = pop_averager(ALLEEG(2),'Criterion','good','SEM','on');
    outPath = fullfile(parentDir,'Results','ERP_stimulus_3blocks'); mkdir(outPath);
    ERP = pop_savemyerp(ERP,'erpname',[EEG.subject '_bin_' strrep(binlister,'.txt','')],'filename',[EEG.subject '.erp'],'filepath',outPath,'Warning','off');
    ALLERP = ERP;
    % eeglab redraw
    % erplab redraw
    
    %% Convert all epochs to fieldtrip format for further processing
    
    EEGft = eeglab2fieldtrip(ALLEEG(2),'preprocessing');
      
    %% Compute and plot ERPs in fieldtrip NOTE: This is where the ERPs start to be computed
    
    % average of all trials
    cfg = [];
    erp_alltrials = ft_timelockanalysis(cfg,EEGft);

    if true 
        binsUnique = sort(unique(epochs_clean(:,3))); % erp for each bin (congruent, incongruent)
        erp_bins = cell(1,length(binsUnique));
        for binI = 1:length(erp_bins) 
            cfg = [];
            cfg.trials = find(epochs_clean(:,3) == binsUnique(binI)); % select trials
            erp_bins{binI} = ft_timelockanalysis(cfg,EEGft); % compute mean
        end

        if plotSave
            cfg = [];
            cfg.xlim = [-0.5 1.0];
            cfg.showlabels = 'yes';
            cfg.comment = 'stimulus-locked (natural, health, taste)';
            cfg.showcomment = 'yes';
            cfg.rotate = 90; % rotate plot
            cfg.fontsize = 16;
            cfg.linewidth = 0.5;
            cfg.layout = 'biosemi64.lay';
            figure(5)
            ft_multiplotER(cfg,erp_bins{:});
            set(gcf,'units','normalized','outerposition',[0 0 1 1],'PaperPositionMode','auto','DefaultTextInterpreter','none','PaperOrientation','portrait'); % maximize figure
            figPath = fullfile(parentDir,'Figures','ERP_stim_3blocks'); mkdir(figPath);
            print(gcf,'-djpeg','-r200', fullfile(figPath,[EEG.subject '_conditions.jpg']));
        end
        close all
    end
    
    %% Time-frequency decomposition in fieldtrip (keep single trials)
    
    cfg = [];
    cfg.channel = {'Fpz' 'F7' 'F8' 'FCz' 'C3' 'C4' 'Pz' 'Oz'}; % all or channels in cell array
    cfg.method = 'wavelet'; % time-freq decomposition method     
    cfg.foi = 1:50;	% freq of interest
    cfg.width = logspace(log10(3),log10(12),length(cfg.foi)); % cycles
    cfg.output = 'fourier';	% fourier, pow, or powandcsd
    cfg.ds = 0.02; % downsampling spacing in seconds
    cfg.ds2 = (1/EEGft.fsample)*(round(0.02/(1/EEGft.fsample))); % actual downsampling spacing based on sampling rate
    cfg.toistartidx = dsearchn(EEGft.time{1}',-0.6); % specify output time begin in seconds
    cfg.toiendidx = dsearchn(EEGft.time{1}',1.5); % specify output time end in seconds
    cfg.toi = EEGft.time{1}(cfg.toistartidx):cfg.ds2:EEGft.time{1}(cfg.toiendidx); % downsampled timepoints to return 
    cfg.keeptrials = 'yes'; % return single trials (yes) or average (no)
    cfg.trials = 'all'; % all trials
    cfg.pad = 'nextpow2'; % pad data to up to next power of 2 (faster more efficient fft)
    tf_fourierSpec = ft_freqanalysis(cfg,EEGft);
    
    if tfrSave
        outPath = fullfile(parentDir,'Results','TFR_fourierSpec_stimulus_3blocks'); mkdir(outPath);
        save(fullfile(outPath,[EEG.subject '_singleTrials.mat']),'tf_fourierSpec');
    end
    
    % prepare objects for single-trial regression later on
    tf_betaCoefs = cell(0); % store data
    
    %% Convert fourier spectrum to power
    
    tf_pow = tf_fourierSpec;
    tf_pow = rmfield(tf_pow,'fourierspctrm');
    tf_pow.fourierspctrm = [];
    tf_pow.powspctrm = abs(tf_fourierSpec.fourierspctrm).^2;
    
    %% Single-trial regression: y ~ b0 + familiar + health + like + taste (block = 1 natural)

    % create design matrix
    colIdx = ismember(epochs_allVars,{'familiar','health','like','taste'}); % regressors
    trialIdx = find(epochs_clean(:,3) == 1); % natural blocks
    designMat = epochs_clean(trialIdx,colIdx);

    % fit model
    cfg = [];
    cfg.designmatrix = epochs_clean(:,colIdx);
    cfg.designmatrix = designMat;
    cfg.intercept = 'yes';
    cfg.trials = trialIdx;
    cfg.model = 'y ~ b0 + familiar + health + like + taste (natural blocks)';
    betaTemp = ft_multipleRegress(cfg,tf_pow);

    tf_betaCoefs{1} = betaTemp;

    %% Single-trial regression: y ~ b0 + familiar + health + like + taste (block = 2 health)

    % create design matrix
    colIdx = ismember(epochs_allVars,{'familiar','health','like','taste'}); % regressors
    trialIdx = find(epochs_clean(:,3) == 2); % health blocks
    designMat = epochs_clean(trialIdx,colIdx);

    % fit model
    cfg = [];
    cfg.designmatrix = epochs_clean(:,colIdx);
    cfg.designmatrix = designMat;
    cfg.intercept = 'yes';
    cfg.trials = trialIdx;
    cfg.model = 'y ~ b0 + familiar + health + like + taste (health blocks)';
    betaTemp = ft_multipleRegress(cfg,tf_pow);

    tf_betaCoefs{2} = betaTemp;

    %% Single-trial regression: y ~ b0 + familiar + health + like + taste (block = 3 taste)

    % create design matrix
    colIdx = ismember(epochs_allVars,{'familiar','health','like','taste'}); % regressors
    trialIdx = find(epochs_clean(:,3) == 3); % taste blocks
    designMat = epochs_clean(trialIdx,colIdx);

    % fit model
    cfg = [];
    cfg.designmatrix = epochs_clean(:,colIdx);
    cfg.designmatrix = designMat;
    cfg.intercept = 'yes';
    cfg.trials = trialIdx;
    cfg.model = 'y ~ b0 + familiar + health + like + taste (taste blocks)';
    betaTemp = ft_multipleRegress(cfg,tf_pow);

    tf_betaCoefs{3} = betaTemp;

    %% MultiplotTFR

    if plotSave 
        fignames = {'natural_block','health_block','taste_block'};
        for j = 1:length(tf_betaCoefs)
            cfg = [];
            cfg.zMax = 2;
            cfg.zlim = [-cfg.zMax cfg.zMax];
            cfg.comment = fignames{j};
            cfg.showlabels = 'yes';
            cfg.rotate = 90;
            cfg.colorbar = 'yes';
            cfg.fontsize = 14;
            cfg.trials = 3; % coefficient number health
            cfg.colormap = 'viridis';

            figure(201); clf
            ft_multiplotTFR(cfg,tf_betaCoefs{j});
            set(gcf,'units','normalized','outerposition',[0 0 1 1],'PaperPositionMode','auto','DefaultTextInterpreter','none','PaperOrientation','portrait'); % maximize figure
            outPath = fullfile(parentDir,'Figures','TFR_pow_stimulus3blocks_beta'); mkdir(outPath);
            tempFigname = fullfile(outPath,[EEG.subject '_multiplotTF_' fignames{j} '_betaHealth.jpg']);
            print(gcf,'-djpeg','-r100', tempFigname);
            close all
            
            cfg = [];
            cfg.zMax = 2;
            cfg.zlim = [-cfg.zMax cfg.zMax];
            cfg.comment = fignames{j};
            cfg.showlabels = 'yes';	
            cfg.rotate = 90;
            cfg.colorbar = 'yes';
            cfg.fontsize = 14;
            cfg.trials = 5; % coefficient number taste
            cfg.colormap = 'viridis';

            figure(201); clf
            ft_multiplotTFR(cfg,tf_betaCoefs{j});
            set(gcf,'units','normalized','outerposition',[0 0 1 1],'PaperPositionMode','auto','DefaultTextInterpreter','none','PaperOrientation','portrait'); % maximize figure
            outPath = fullfile(parentDir,'Figures','TFR_pow_stimulus3blocks_beta'); mkdir(outPath);
            tempFigname = fullfile(outPath,[EEG.subject '_multiplotTF_' fignames{j} '_betaTaste.jpg']);
            print(gcf,'-djpeg','-r100', tempFigname);
            close all
        end
    end


    %% plot FCz

    if plotSave
        figure(101); clf
        set(gcf,'units','normalized','outerposition',[0 0 1 1],'PaperPositionMode','auto','DefaultTextInterpreter','none','PaperOrientation','portrait'); % maximize figure
        for j = 1:length(tf_betaCoefs)
            cfg = [];
            cfg.chan = 'FCz';
            cfg.xlim = [-0.5 1.5];
            cfg.trials = 3; % health coefficient 
            cfg.subplot = [2,3,j];
            cfg.fontsize = 14;
            cfg.colormap = 'viridis';
            cfg.title = {[cfg.chan ' health beta'],tf_betaCoefs{j}.cfg.regressparams.model};
            ft_contourfTFR(cfg,tf_betaCoefs{j});
        end
        
        for j = 1:length(tf_betaCoefs)
            cfg = [];
            cfg.chan = 'FCz';
            cfg.xlim = [-0.5 1.5];
            cfg.trials = 5; % taste coefficient 
            cfg.subplot = [2,3,j+3];
            cfg.fontsize = 14;
            cfg.colormap = 'viridis';
            cfg.title = {[cfg.chan ' taste beta'],tf_betaCoefs{j}.cfg.regressparams.model};
            ft_contourfTFR(cfg,tf_betaCoefs{j});
        end
        
        outPath = fullfile(parentDir,'Figures','TFR_pow_stimulus3blocks_beta'); mkdir(outPath);
        tempFigname = fullfile(outPath,[EEG.subject '_FCz_' fignames{j} '_betaHealthTaste.jpg']);
        print(gcf,'-djpeg','-r100', tempFigname);
        close all
    end
    
    %% Plot and save stuff 
    
    if plotSave 
        
        % average ERPs in every channel eeglab: plot, channel ERP, rect array
        figure(1); clf; 
        set(gcf,'units','normalized','outerposition',[0 0 1 1],'PaperPositionMode','auto','DefaultTextInterpreter','none'); % maximize figure
        pop_plottopo(ALLEEG(2),1:EEG.nbchan,[EEG.subject ' average ERPs'],0,'ydir',1);
        set(gcf,'units','normalized','outerposition',[0 0 1 1],'PaperPositionMode','auto','DefaultTextInterpreter','none'); % maximize figure
        outPath = fullfile(parentDir,'Figures','ERP_stim_3blocks'); mkdir(outPath);
        tempFigname = fullfile(outPath,[EEG.subject '_conditionAvg.jpg']);
        print(gcf,'-djpeg','-r100',tempFigname);

        % Butterfly plot with scale map using eeglab: plot, channel ERP, with scale maps
        figure(2); clf; 
        set(gcf,'units','normalized','outerposition',[0 0 1 1],'PaperPositionMode','auto','DefaultTextInterpreter','none'); % maximize figure
        pop_timtopo(ALLEEG(2),[-200 1400],[-200:200:1400],'ERP data and scalp maps');
        set(gcf,'units','normalized','outerposition',[0 0 1 1],'PaperPositionMode','auto','DefaultTextInterpreter','none'); % maximize figure
        tempFigname = fullfile(outPath,[EEG.subject '_conditionAvg_butterflyScalpMap.jpg']);
        print(gcf,'-djpeg','-r100',tempFigname);
        
        % topographical map using eeglab: plot, ERP map series in 2D
        pop_topoplot(ALLEEG(2),1,[-200:100:1400],[EEG.subject ' topographical maps'],[5 5],0,'electrodes','on');
        set(gcf,'units','normalized','outerposition',[0 0 1 1],'PaperPositionMode','auto','DefaultTextInterpreter','none'); % maximize figure
        tempFigname = fullfile(outPath,[EEG.subject '_conditionAvg_topo.jpg']);
        print(gcf,'-djpeg','-r100',tempFigname);
        
    end 
    
    %% Save beta coefficients
    
    tf_betaCoefs;
    outPath = fullfile(parentDir,'Results','TFR_pow_stimulus_beta_familiarHealthLikeTaste'); mkdir(outPath);
    save(fullfile(outPath,[EEG.subject '.mat']),'tf_betaCoefs');
    
    %% Power for each bin
    
    tempTF = tf_pow;
    tempTF.powspctrm = [];
    tempTF.cumtapcnt = [];
    tempTF.dimord = 'chan_freq_time';

    % time-freq for each bin
    binsUnique = sort(unique(epochs_clean(:,3))); % unique bins
    tf_bins = cell(1,length(binsUnique)); % create empty cell to store bin raw data
    tf_bins_dBNorm = cell(size(tf_bins)); % create empty cell to store bin db-normalized data 
    for binI = 1:length(tf_bins) % run time-freq decomposition for each bin
        % compute mean time-freq for each bin
        tempTF.cfg.trials = find(epochs_clean(:,3) == binsUnique(binI)); % select trials
        tempTF.powspctrm = squeeze(mean(tf_pow.powspctrm(tempTF.cfg.trials,:,:,:),1));
        tf_bins{binI} = tempTF;

        % baseline correction
        cfg = [];
        cfg.baseline = [-0.5 -0.3]; % baseline window
        cfg.baselinetype = 'db'; % baseline correction type
        cfg.parameter = 'powspctrm'; 
        tf_bins_dBNorm{binI} = ft_freqbaseline(cfg,tf_bins{binI});
    end

    % save tf output
    outPath = fullfile(parentDir,'Results','TFR_pow_stimulus_3blocks'); mkdir(outPath);
    save(fullfile(outPath,[EEG.subject '_avgPow.mat']),'tf_bins','tf_bins_dBNorm');

    if plotSave
        fignames = {'natural_block','health_block','taste_block'};
        for binI = 1:length(tf_bins_dBNorm) 
%             cfg = [];
%             cfg.zMax = max(max(max(tf_bins_dBNorm{binI}.powspctrm))) / 2;
%             cfg.zlim = [-cfg.zMax cfg.zMax];
%             cfg.comment = fignames{binI};
%             cfg.xlim = [-0.5 1.5];
%             cfg.showlabels = 'yes';	
%             cfg.rotate = 90;
%             cfg.colorbar = 'yes';
%             cfg.fontsize = 14;
%             cfg.colormap = 'viridis';
% 
%             figure(201); clf
%             ft_multiplotTFR(cfg,tf_bins_dBNorm{binI});
%             set(gcf,'units','normalized','outerposition',[0 0 1 1],'PaperPositionMode','auto','DefaultTextInterpreter','none','PaperOrientation','portrait'); % maximize figure
%             
%             outPath = fullfile(parentDir,'Figures','TFR_pow_stimulus3blocks'); mkdir(outPath);
%             tempFigname = fullfile(outPath,[EEG.subject '_multiplotTF_avgPow_' fignames{binI} '.jpg']);
%             print(gcf,'-djpeg','-r100', tempFigname);
           
            % plot all channels (maximized and log scale)
            figure(202); clf
            set(gcf,'units','normalized','outerposition',[0 0 1 1],'PaperPositionMode','auto','DefaultTextInterpreter','none','PaperOrientation','portrait'); % maximize figure
            chans = tf_bins_dBNorm{binI}.label;
            chansSubplotIdx = [2 5 4 6 7 9 8 11];
            for j = 1:size(tf_bins_dBNorm{binI}.powspctrm,1)
                cfg = [];
                cfg.chan = tf_bins_dBNorm{binI}.label{j};
                cfg.xlim = [-0.5 1.5];
                cfg.subplot = [4,3,chansSubplotIdx(j)];
                cfg.fontsize = 12;
                cfg.colorbar = 'yes';
                cfg.colormap = 'viridis';
                cfg.title = {[cfg.chan ' power ' fignames{binI}]};
                ft_contourfTFR(cfg,tf_bins_dBNorm{binI});
            end
            outPath = fullfile(parentDir,'Figures','TFR_pow_stimulus3blocks'); mkdir(outPath);
            tempFigname = fullfile(outPath,[EEG.subject '_multiplotTF_avgPow_' fignames{binI} '.jpg']);
            print(gcf,'-djpeg','-r100', tempFigname);
            close all
        end
    end

    %% Save parameters
    
    params.workingdirectory = parentDir;
    params.binlister = fullfile(parentDir,'Binlister',binlister);
    params.epochRange = epochRange; % ms
    params.epochBaselineCorrect = epochBaselineCorrect;

    save(fullfile(parentDir,'Binlister',[strrep(binlister,'.txt','') '_epochingParams.mat']),'params');

    %% Done
    
    disp(['Finished subject ' subject, '!']);
    dlmwrite(fullfile(parentDir,'Messages',['Finished_Subject_' subject ' ' datestr(datetime('now')) '.txt']),['Finished!' ' ' datestr(datetime('now'))],'delimiter','');

catch ME % if errors when runnig script, catch them
    disp(['Error with subject ' subject, '!']);
    save(fullfile(parentDir,'Messages',['Error_MException_' subject ' ' datestr(datetime('now')) '.mat']),'ME'); % save MException object 
end

clear
close all

end % end function