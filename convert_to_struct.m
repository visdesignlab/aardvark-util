for index = 1:length(Cells)
    Cells_Struct(index) = struct(Cells(index))
end

% transpose ii_stored and segID because they are flipped for some resoun in source data
for index = 1:length(Cells_Struct)
    Cells_Struct(index).ii_stored  = Cells_Struct(index).ii_stored.'
    Cells_Struct(index).segID  = Cells_Struct(index).segID.'
end


% for index = 1:length(Well2_Cells)
%     Well2_Cells_Struct(index) = struct(Well2_Cells(index))
% end
% 
% for index = 1:length(Well4_Cells)
%     Well4_Cells_Struct(index) = struct(Well4_Cells(index))
% end
% 
% for index = 1:length(Well5_Cells)
%     Well5_Cells_Struct(index) = struct(Well5_Cells(index))
% end